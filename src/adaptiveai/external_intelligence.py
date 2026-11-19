from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from adaptiveai.capabilities import CapabilityProfile
from adaptiveai.evidence import EvidenceRecord, Reliability
from adaptiveai.hf_benchmark import ImportResult
from adaptiveai.identity_resolution import IdentityResolution, ResolutionStatus


class CoverageReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    total_source_records: int
    accepted_records: int
    rejected_records: int
    unique_source_model_ids: int
    resolved_canonical_models: int
    unresolved_models: int
    benchmarks: dict[str, int]
    metrics: dict[str, int]
    exact_revisions: int
    unknown_revisions: int
    complete_provenance: int
    missing_important_metadata: int
    verified_records: int
    redistribution_unknown: int


def coverage_report(
    result: ImportResult, resolutions: tuple[IdentityResolution, ...]
) -> CoverageReport:
    records = result.records
    resolved = {
        item.model.canonical_id
        for item in resolutions
        if item.status in {ResolutionStatus.EXACT, ResolutionStatus.VERIFIED_ALIAS}
        and item.model is not None
    }
    unresolved = {
        item.source_model_id
        for item in resolutions
        if item.status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.AMBIGUOUS}
    }
    return CoverageReport(
        total_source_records=result.manifest.source_records,
        accepted_records=len(records),
        rejected_records=len(result.diagnostics),
        unique_source_model_ids=len({record.source_model_id for record in records}),
        resolved_canonical_models=len(resolved),
        unresolved_models=len(unresolved),
        benchmarks=dict(Counter(record.benchmark or "unknown" for record in records)),
        metrics=dict(Counter(record.metric or "unknown" for record in records)),
        exact_revisions=sum(
            record.subject.model.revision.revision is not None for record in records
        ),
        unknown_revisions=sum(record.subject.model.revision.revision is None for record in records),
        complete_provenance=sum(
            bool(record.provenance and record.source_uri and record.source_record_id)
            for record in records
        ),
        missing_important_metadata=sum(
            record.subject.model.revision.revision is None
            or record.subject.configuration.harness_version == "unknown"
            for record in records
        ),
        verified_records=sum(record.reliability == Reliability.VERIFIED for record in records),
        redistribution_unknown=sum(
            record.permissions.redistribution.value == "unknown" for record in records
        ),
    )


def build_external_profile(
    record: EvidenceRecord, *, profile_version: int = 1
) -> CapabilityProfile:
    return CapabilityProfile(
        profile_id=f"external-{record.subject.model.canonical_id}",
        profile_version=profile_version,
        model=record.subject.model,
        created_at=record.retrieved_at,
        benchmark_evidence_ids=(record.evidence_id,),
        missing_information=(
            "context_window_tokens",
            "input_modalities",
            "output_modalities",
            "tool_use",
            "structured_output",
            "exact_model_revision",
            "agent_scaffold",
        ),
    )


def write_private_snapshot(result: ImportResult, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"{result.manifest.snapshot_id}.json"
    manifest_path = directory / f"{result.manifest.snapshot_id}.manifest.json"
    if raw_path.exists() and raw_path.read_bytes() != result.raw_bytes:
        raise FileExistsError(f"immutable snapshot collision: {raw_path}")
    serialized_manifest = result.manifest.model_dump_json(indent=2) + "\n"
    if manifest_path.exists() and manifest_path.read_text() != serialized_manifest:
        raise FileExistsError(f"immutable manifest collision: {manifest_path}")
    raw_path.write_bytes(result.raw_bytes)
    manifest_path.write_text(serialized_manifest)
    return raw_path, manifest_path


def snapshot_changed(current_sha256: str, previous_sha256: str | None) -> bool:
    return previous_sha256 is not None and current_sha256 != previous_sha256


def profile_summary(profile: CapabilityProfile, records: tuple[EvidenceRecord, ...]) -> dict:
    evidence = [
        record for record in records if record.evidence_id in profile.benchmark_evidence_ids
    ]
    conflicts = []
    by_key: dict[tuple[str | None, str | None], set[str]] = {}
    for record in evidence:
        key = (record.benchmark, record.metric)
        by_key.setdefault(key, set()).add(json.dumps(record.value, sort_keys=True))
    for key, values in by_key.items():
        if len(values) > 1:
            conflicts.append({"benchmark": key[0], "metric": key[1], "values": sorted(values)})
    return {
        "profile_id": profile.profile_id,
        "model_id": profile.model.canonical_id,
        "known_results": len(evidence),
        "sources": sorted({record.source_id for record in evidence}),
        "verified_results": sum(record.reliability == Reliability.VERIFIED for record in evidence),
        "retrieved_at": sorted({record.retrieved_at.isoformat() for record in evidence}),
        "unknown_capabilities": list(profile.missing_information),
        "conflicts": conflicts,
    }
