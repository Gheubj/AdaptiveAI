from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class PermissionState(StrEnum):
    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class SourcePermissions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metadata_access: PermissionState = PermissionState.UNKNOWN
    local_ingestion: PermissionState = PermissionState.UNKNOWN
    local_analysis: PermissionState = PermissionState.UNKNOWN
    derived_use: PermissionState = PermissionState.UNKNOWN
    redistribution: PermissionState = PermissionState.UNKNOWN
    attribution_required: bool | None = None
    attribution_text: str | None = None
    commercial_use: PermissionState = PermissionState.UNKNOWN
    notes: tuple[str, ...] = ()


class ExportDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: bool
    reasons: tuple[str, ...]


def evaluate_export(permissions: SourcePermissions) -> ExportDecision:
    reasons: list[str] = []
    if permissions.redistribution != PermissionState.ALLOWED:
        reasons.append(f"redistribution_{permissions.redistribution.value}")
    if permissions.attribution_required is None:
        reasons.append("attribution_requirement_unknown")
    elif permissions.attribution_required and not permissions.attribution_text:
        reasons.append("required_attribution_missing")
    return ExportDecision(allowed=not reasons, reasons=tuple(reasons))
