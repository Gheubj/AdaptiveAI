from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from adaptiveai.capabilities import CapabilityProfile, SupportState
from adaptiveai.identity import DeploymentIdentity


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"


class ReasonCode(StrEnum):
    UNAVAILABLE = "unavailable"
    AVAILABILITY_UNKNOWN = "availability_unknown"
    LOCAL_ONLY = "local_only"
    PROVIDER_NOT_ALLOWED = "provider_not_allowed"
    MODEL_NOT_ALLOWED = "model_not_allowed"
    MODALITY_UNSUPPORTED = "modality_unsupported"
    MODALITY_UNKNOWN = "modality_unknown"
    TOOLS_UNSUPPORTED = "tools_unsupported"
    TOOLS_UNKNOWN = "tools_unknown"
    CONTEXT_TOO_SMALL = "context_too_small"
    CONTEXT_UNKNOWN = "context_unknown"
    MEMORY_EXCEEDED = "memory_exceeded"
    MEMORY_UNKNOWN = "memory_unknown"


class DeploymentState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    deployment: DeploymentIdentity
    local: bool
    available: bool | None = None
    memory_bytes: int | None = Field(default=None, ge=0)


class EligibilityConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    local_only: bool = False
    allowed_providers: frozenset[str] | None = None
    allowed_models: frozenset[str] | None = None
    required_input_modalities: frozenset[str] = frozenset()
    require_tools: bool = False
    minimum_context_tokens: int | None = Field(default=None, ge=1)
    available_memory_bytes: int | None = Field(default=None, ge=0)


class EligibilityReason(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: ReasonCode
    detail: str


class EligibilityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: EligibilityStatus
    reasons: tuple[EligibilityReason, ...]


def evaluate_eligibility(
    profile: CapabilityProfile,
    deployment: DeploymentState,
    constraints: EligibilityConstraints,
) -> EligibilityDecision:
    hard: list[EligibilityReason] = []
    unknown: list[EligibilityReason] = []

    def add(target: list[EligibilityReason], code: ReasonCode, detail: str) -> None:
        target.append(EligibilityReason(code=code, detail=detail))

    if deployment.available is False:
        add(hard, ReasonCode.UNAVAILABLE, "deployment reports unavailable")
    elif deployment.available is None:
        add(unknown, ReasonCode.AVAILABILITY_UNKNOWN, "deployment availability is unknown")
    if constraints.local_only and not deployment.local:
        add(hard, ReasonCode.LOCAL_ONLY, "non-local deployment violates local-only constraint")
    provider = deployment.deployment.provider.canonical_id
    if constraints.allowed_providers is not None and provider not in constraints.allowed_providers:
        add(hard, ReasonCode.PROVIDER_NOT_ALLOWED, f"provider {provider} is not allowed")
    model = profile.model.canonical_id
    if constraints.allowed_models is not None and model not in constraints.allowed_models:
        add(hard, ReasonCode.MODEL_NOT_ALLOWED, f"model {model} is not allowed")
    for modality in sorted(constraints.required_input_modalities):
        state = profile.input_modalities.get(modality)
        if state is None or state.state == SupportState.UNKNOWN:
            add(unknown, ReasonCode.MODALITY_UNKNOWN, f"input modality {modality} is unknown")
        elif state.state == SupportState.UNSUPPORTED:
            add(hard, ReasonCode.MODALITY_UNSUPPORTED, f"input modality {modality} unsupported")
    if constraints.require_tools:
        if profile.tool_use.state == SupportState.UNSUPPORTED:
            add(hard, ReasonCode.TOOLS_UNSUPPORTED, "tool use unsupported")
        elif profile.tool_use.state == SupportState.UNKNOWN:
            add(unknown, ReasonCode.TOOLS_UNKNOWN, "tool use support unknown")
    if constraints.minimum_context_tokens is not None:
        if profile.context_window_tokens is None:
            add(unknown, ReasonCode.CONTEXT_UNKNOWN, "context window unknown")
        elif profile.context_window_tokens < constraints.minimum_context_tokens:
            add(hard, ReasonCode.CONTEXT_TOO_SMALL, "context window below required minimum")
    if constraints.available_memory_bytes is not None:
        if deployment.memory_bytes is None:
            add(unknown, ReasonCode.MEMORY_UNKNOWN, "deployment memory requirement unknown")
        elif deployment.memory_bytes > constraints.available_memory_bytes:
            add(hard, ReasonCode.MEMORY_EXCEEDED, "deployment exceeds available memory")
    reasons = tuple(hard + unknown)
    if hard:
        return EligibilityDecision(status=EligibilityStatus.INELIGIBLE, reasons=reasons)
    if unknown:
        return EligibilityDecision(status=EligibilityStatus.UNKNOWN, reasons=reasons)
    return EligibilityDecision(status=EligibilityStatus.ELIGIBLE, reasons=())
