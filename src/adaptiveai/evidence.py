from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from adaptiveai.identity import EvaluationSubject
from adaptiveai.permissions import SourcePermissions


class EvidenceType(StrEnum):
    PROVIDER_METADATA = "provider_metadata"
    EXTERNAL_AGGREGATE = "external_aggregate"
    EXTERNAL_INSTANCE = "external_instance"
    LOCAL_EVALUATION = "local_evaluation"
    LATENCY = "latency"
    COST = "cost"
    CAPABILITY_CLAIM = "capability_claim"


class Reliability(StrEnum):
    VERIFIED = "verified"
    REPRODUCED = "reproduced"
    DECLARED = "declared"
    UNVERIFIED = "unverified"


class SystemKind(StrEnum):
    BASE_MODEL = "base_model"
    PROVIDER_DEPLOYMENT = "provider_deployment"
    ROUTED_SYSTEM = "routed_system"


class MissingValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    field: str
    reason: str


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_type: EvidenceType
    source_id: str
    source_version: str | None = None
    source_uri: str | None = None
    source_record_id: str | None = None
    source_model_id: str | None = None
    evaluation_date: datetime | None = None
    retrieved_at: datetime
    subject: EvaluationSubject
    system_kind: SystemKind
    benchmark: str | None = None
    benchmark_version: str | None = None
    task_distribution: str | None = None
    method: str
    metric: str | None = None
    value: float | int | str | bool | None = None
    units: str | None = None
    scale: str | None = None
    sample_size: int | None = Field(default=None, ge=1)
    provenance: tuple[str, ...] = ()
    reliability: Reliability
    permissions: SourcePermissions = Field(default_factory=SourcePermissions)
    missing: tuple[MissingValue, ...] = ()

    @model_validator(mode="after")
    def missingness_is_explicit(self) -> EvidenceRecord:
        missing_fields = {item.field for item in self.missing}
        for field in ("source_version", "metric", "value", "units"):
            if getattr(self, field) is None and field not in missing_fields:
                raise ValueError(f"{field} is absent but not declared in missing")
            if getattr(self, field) is not None and field in missing_fields:
                raise ValueError(f"{field} has both a value and a missing declaration")
        return self

    @property
    def evidence_id(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return "ev-" + hashlib.sha256(payload.encode()).hexdigest()


class ComparabilityDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    comparable: bool
    mismatches: tuple[str, ...]


def compare_evidence(left: EvidenceRecord, right: EvidenceRecord) -> ComparabilityDiagnostic:
    checks = {
        "benchmark": (left.benchmark, right.benchmark),
        "benchmark_version": (left.benchmark_version, right.benchmark_version),
        "task_distribution": (left.task_distribution, right.task_distribution),
        "metric": (left.metric, right.metric),
        "units": (left.units, right.units),
        "scale": (left.scale, right.scale),
        "harness": (
            left.subject.configuration.harness,
            right.subject.configuration.harness,
        ),
        "harness_version": (
            left.subject.configuration.harness_version,
            right.subject.configuration.harness_version,
        ),
        "evaluation_configuration": (
            left.subject.configuration.fingerprint,
            right.subject.configuration.fingerprint,
        ),
        "model_revision": (
            left.subject.model.revision.revision,
            right.subject.model.revision.revision,
        ),
        "system_kind": (left.system_kind, right.system_kind),
    }
    mismatches = tuple(name for name, pair in checks.items() if pair[0] != pair[1])
    return ComparabilityDiagnostic(comparable=not mismatches, mismatches=mismatches)


def index_evidence(records: tuple[EvidenceRecord, ...]) -> dict[str, EvidenceRecord]:
    indexed: dict[str, EvidenceRecord] = {}
    for record in records:
        if record.evidence_id in indexed:
            raise ValueError(f"duplicate evidence: {record.evidence_id}")
        indexed[record.evidence_id] = record
    return indexed
