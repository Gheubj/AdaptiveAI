from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from adaptiveai.evidence import EvidenceRecord, EvidenceType, Reliability, SystemKind
from adaptiveai.identity import (
    EvaluationConfiguration,
    EvaluationSubject,
    ModelFamily,
    ModelIdentity,
)
from adaptiveai.permissions import PermissionState, SourcePermissions

SOURCE_ID = "huggingface:SWE-bench/SWE-bench_Verified:leaderboard"
SOURCE_URL = "https://huggingface.co/api/datasets/SWE-bench/SWE-bench_Verified/leaderboard"


class ImportErrorCode(StrEnum):
    NETWORK = "network_error"
    HTTP = "http_error"
    RATE_LIMIT = "rate_limit"
    RESPONSE_TOO_LARGE = "response_too_large"
    MALFORMED_JSON = "malformed_json"
    SCHEMA = "schema_error"
    EMPTY = "empty_leaderboard"


class BenchmarkImportError(RuntimeError):
    def __init__(self, code: ImportErrorCode, message: str, *, partial: bool = False):
        super().__init__(message)
        self.code = code
        self.partial = partial


class HuggingFaceLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    max_results: int = Field(20, ge=1, le=1000)
    max_download_bytes: int = Field(1_048_576, ge=1024, le=10_485_760)
    connect_timeout_seconds: float = Field(5, gt=0, le=60)
    read_timeout_seconds: float = Field(20, gt=0, le=120)
    retry_limit: int = Field(1, ge=0, le=3)
    total_request_limit: int = Field(1, ge=1, le=3)
    offline: bool = False


class HFLeaderboardEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    rank: int = Field(ge=1)
    filename: str | None = None
    value: float
    verified: bool = False
    source: dict[str, Any] | None = None
    pullRequest: int | None = None
    modelId: str = Field(min_length=3)
    lower_is_better: bool = False


class SnapshotManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    snapshot_id: str
    source_id: str
    retrieved_at: datetime
    sha256: str
    size_bytes: int
    schema_version: str = "1.0"
    parser_version: str = "1.0"
    import_status: str
    source_records: int
    accepted_records: int
    rejected_records: int
    incomplete: bool


class ImportDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int
    code: str
    message: str


@dataclass(frozen=True)
class ImportResult:
    manifest: SnapshotManifest
    records: tuple[EvidenceRecord, ...]
    diagnostics: tuple[ImportDiagnostic, ...]
    raw_bytes: bytes


def swe_bench_permissions() -> SourcePermissions:
    return SourcePermissions(
        metadata_access=PermissionState.ALLOWED,
        local_ingestion=PermissionState.ALLOWED,
        local_analysis=PermissionState.ALLOWED,
        derived_use=PermissionState.ALLOWED,
        redistribution=PermissionState.UNKNOWN,
        attribution_required=True,
        attribution_text=(
            "Hugging Face Hub leaderboard API; SWE-bench Verified by the SWE-bench team"
        ),
        commercial_use=PermissionState.UNKNOWN,
        notes=(
            "API documentation permits analysis/tooling; leaderboard-data redistribution is not "
            "explicitly licensed in the reviewed interfaces.",
            "Scores describe submitted model/agent systems, not isolated base-model quality.",
        ),
    )


class HuggingFaceSWEVerifiedAdapter:
    adapter_id = "hf-swe-bench-verified"
    adapter_version = "1.0"

    def __init__(self, limits: HuggingFaceLimits | None = None):
        self.limits = limits or HuggingFaceLimits()

    def fetch(self, *, transport: httpx.BaseTransport | None = None) -> bytes:
        if self.limits.offline:
            raise BenchmarkImportError(ImportErrorCode.NETWORK, "adapter is in offline mode")
        timeout = httpx.Timeout(
            self.limits.read_timeout_seconds, connect=self.limits.connect_timeout_seconds
        )
        attempts = min(self.limits.retry_limit + 1, self.limits.total_request_limit)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=timeout, transport=transport) as client:
                    with client.stream(
                        "GET", SOURCE_URL, headers={"Accept": "application/json"}
                    ) as response:
                        if response.status_code == 429:
                            raise BenchmarkImportError(ImportErrorCode.RATE_LIMIT, "rate limited")
                        response.raise_for_status()
                        chunks: list[bytes] = []
                        size = 0
                        for chunk in response.iter_bytes():
                            size += len(chunk)
                            if size > self.limits.max_download_bytes:
                                raise BenchmarkImportError(
                                    ImportErrorCode.RESPONSE_TOO_LARGE,
                                    f"response exceeds {self.limits.max_download_bytes} bytes",
                                    partial=True,
                                )
                            chunks.append(chunk)
                        return b"".join(chunks)
            except BenchmarkImportError:
                raise
            except httpx.HTTPStatusError as error:
                raise BenchmarkImportError(ImportErrorCode.HTTP, str(error)) from error
            except (httpx.TimeoutException, httpx.NetworkError) as error:
                last_error = error
                if attempt + 1 == attempts:
                    break
        raise BenchmarkImportError(ImportErrorCode.NETWORK, str(last_error)) from last_error

    def import_bytes(self, raw: bytes, *, retrieved_at: datetime | None = None) -> ImportResult:
        retrieved_at = retrieved_at or datetime.now(UTC)
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BenchmarkImportError(ImportErrorCode.MALFORMED_JSON, str(error)) from error
        if not isinstance(payload, list):
            raise BenchmarkImportError(
                ImportErrorCode.SCHEMA, "leaderboard response must be a list"
            )
        if not payload:
            raise BenchmarkImportError(ImportErrorCode.EMPTY, "leaderboard is empty")
        digest = hashlib.sha256(raw).hexdigest()
        records: list[EvidenceRecord] = []
        diagnostics: list[ImportDiagnostic] = []
        for index, item in enumerate(payload[: self.limits.max_results]):
            try:
                entry = HFLeaderboardEntry.model_validate(item)
                records.append(self._normalize(entry, digest, retrieved_at))
            except (ValidationError, ValueError) as error:
                diagnostics.append(
                    ImportDiagnostic(index=index, code="rejected_entry", message=str(error))
                )
        limited = len(payload) > self.limits.max_results
        status = "complete" if not diagnostics and not limited else "incomplete"
        manifest = SnapshotManifest(
            snapshot_id=f"hf-swe-verified-{digest[:16]}",
            source_id=SOURCE_ID,
            retrieved_at=retrieved_at,
            sha256=digest,
            size_bytes=len(raw),
            import_status=status,
            source_records=len(payload),
            accepted_records=len(records),
            rejected_records=len(diagnostics),
            incomplete=bool(diagnostics or limited),
        )
        return ImportResult(manifest, tuple(records), tuple(diagnostics), raw)

    def _normalize(
        self, entry: HFLeaderboardEntry, snapshot_sha: str, retrieved_at: datetime
    ) -> EvidenceRecord:
        namespace, separator, model_name = entry.modelId.partition("/")
        if not separator:
            raise ValueError("modelId must be a namespace/name Hugging Face identifier")
        identity = ModelIdentity(
            family=ModelFamily(namespace=namespace, family=model_name), model=model_name
        )
        config = EvaluationConfiguration(
            harness="SWE-bench Verified leaderboard submission",
            harness_version="unknown",
            parameters={
                "agent_scaffold": "unknown",
                "lower_is_better": entry.lower_is_better,
            },
        )
        source_url = entry.source.get("url") if entry.source else None
        record_id = f"{entry.modelId}:{entry.filename or entry.rank}:{entry.pullRequest or 'none'}"
        return EvidenceRecord(
            evidence_type=EvidenceType.EXTERNAL_AGGREGATE,
            source_id=SOURCE_ID,
            source_version=snapshot_sha,
            source_uri=source_url or SOURCE_URL,
            source_record_id=record_id,
            source_model_id=entry.modelId,
            retrieved_at=retrieved_at,
            subject=EvaluationSubject(model=identity, configuration=config),
            system_kind=SystemKind.ROUTED_SYSTEM,
            benchmark="SWE-bench Verified",
            benchmark_version="verified-500",
            task_distribution="500 human-verified GitHub issue resolution tasks",
            method="official Hugging Face dataset leaderboard aggregate",
            metric="resolved",
            value=entry.value,
            units="percent",
            scale="0..100",
            sample_size=500,
            provenance=(SOURCE_URL, record_id),
            reliability=Reliability.VERIFIED if entry.verified else Reliability.DECLARED,
            permissions=swe_bench_permissions(),
        )

    def fetch_and_import(self, *, transport: httpx.BaseTransport | None = None) -> ImportResult:
        return self.import_bytes(self.fetch(transport=transport))
