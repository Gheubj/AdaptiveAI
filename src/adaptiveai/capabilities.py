from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from adaptiveai.evidence import EvidenceRecord, compare_evidence
from adaptiveai.identity import ModelIdentity


class SupportState(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class CapabilityValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: SupportState = SupportState.UNKNOWN
    evidence_ids: tuple[str, ...] = ()


class CapabilityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    profile_id: str
    profile_version: int = Field(ge=1)
    model: ModelIdentity
    created_at: datetime
    input_modalities: dict[str, CapabilityValue] = Field(default_factory=dict)
    output_modalities: dict[str, CapabilityValue] = Field(default_factory=dict)
    tool_use: CapabilityValue = Field(default_factory=CapabilityValue)
    structured_output: CapabilityValue = Field(default_factory=CapabilityValue)
    context_window_tokens: int | None = Field(default=None, ge=1)
    context_window_evidence_ids: tuple[str, ...] = ()
    benchmark_evidence_ids: tuple[str, ...] = ()
    deployment_ids: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()

    @model_validator(mode="after")
    def context_missingness(self) -> CapabilityProfile:
        missing = set(self.missing_information)
        if self.context_window_tokens is None and "context_window_tokens" not in missing:
            raise ValueError("unknown context window must be explicit")
        if self.context_window_tokens is not None and "context_window_tokens" in missing:
            raise ValueError("context window cannot be both known and missing")
        return self


def validate_profile_evidence(
    profile: CapabilityProfile, evidence: dict[str, EvidenceRecord]
) -> tuple[str, ...]:
    referenced = set(profile.benchmark_evidence_ids) | set(profile.context_window_evidence_ids)
    referenced.update(profile.tool_use.evidence_ids)
    referenced.update(profile.structured_output.evidence_ids)
    for value in (*profile.input_modalities.values(), *profile.output_modalities.values()):
        referenced.update(value.evidence_ids)
    missing = sorted(referenced - evidence.keys())
    if missing:
        raise ValueError(f"profile references unknown evidence: {missing}")
    wrong_model = sorted(
        evidence_id
        for evidence_id in referenced
        if evidence[evidence_id].subject.model != profile.model
    )
    if wrong_model:
        raise ValueError(f"profile evidence belongs to another model: {wrong_model}")
    records = [evidence[item] for item in profile.benchmark_evidence_ids]
    mismatches: set[str] = set()
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            diagnostic = compare_evidence(left, right)
            mismatches.update(diagnostic.mismatches)
    return tuple(sorted(mismatches))
