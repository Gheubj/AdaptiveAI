from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from adaptiveai.identity import EvaluationConfiguration, ModelIdentity
from adaptiveai.permissions import SourcePermissions


class RoutingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceClass(StrEnum):
    MODEL_CAPABILITY = "model_capability"
    ROUTING_SUPERVISION = "routing_supervision"


class DataRole(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    EXPLORATORY_TEST = "exploratory_test"
    CONFIRMATORY_TEST = "confirmatory_test"


class SubjectKind(StrEnum):
    MODEL = "model"
    PROVIDER_DEPLOYMENT = "provider_deployment"
    AGENT_SYSTEM = "agent_system"


class RoutingDatasetDescriptor(RoutingModel):
    dataset_id: str
    source_revision: str
    adapter_version: str
    permissions: SourcePermissions
    available_splits: tuple[str, ...]
    subject_kind: SubjectKind


class RoutingQuery(RoutingModel):
    query_id: str
    split: str
    data_role: DataRole
    task_family: str
    task_name: str
    metric_id: str
    metric_units: str
    metric_scale: str
    content: str | None = None
    content_reference: str | None = None
    ground_truth: str | tuple[str, ...] | None = None
    provenance: tuple[str, ...]

    @model_validator(mode="after")
    def content_or_reference(self) -> RoutingQuery:
        if not self.content and not self.content_reference:
            raise ValueError("query requires content or an authorized content reference")
        return self

    @property
    def content_hash(self) -> str | None:
        if self.content is None:
            return None
        normalized = " ".join(self.content.casefold().split())
        return hashlib.sha256(normalized.encode()).hexdigest()


class RoutingCandidate(RoutingModel):
    candidate_id: str
    source_model_id: str
    model_identity: ModelIdentity | None = None
    provider: str | None = None
    deployment: str | None = None
    quantization: str | None = None
    exact_revision_known: bool = False
    historical_only: bool = True

    @model_validator(mode="after")
    def revision_is_honest(self) -> RoutingCandidate:
        has_revision = bool(
            self.model_identity and self.model_identity.revision.revision is not None
        )
        if self.exact_revision_known != has_revision:
            raise ValueError("exact_revision_known must match the model identity revision")
        return self


class RoutingOutcome(RoutingModel):
    evidence_class: EvidenceClass = EvidenceClass.ROUTING_SUPERVISION
    query_id: str
    candidate_id: str
    score: float
    metric_id: str
    metric_units: str
    metric_scale: str
    evaluation: EvaluationConfiguration
    response: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    latency_seconds: float | None = Field(default=None, ge=0)
    historical_cost_usd: float | None = Field(default=None, ge=0)
    price_source: str | None = None
    provenance: tuple[str, ...]
    permissions: SourcePermissions
    missing: tuple[str, ...] = ()

    @model_validator(mode="after")
    def missingness_is_explicit(self) -> RoutingOutcome:
        for field in (
            "response",
            "input_tokens",
            "output_tokens",
            "latency_seconds",
            "historical_cost_usd",
            "price_source",
        ):
            value = getattr(self, field)
            if value is None and field not in self.missing:
                raise ValueError(f"{field} is absent but not declared missing")
            if value is not None and field in self.missing:
                raise ValueError(f"{field} is both present and declared missing")
        return self

    @property
    def outcome_id(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return "route-" + hashlib.sha256(payload.encode()).hexdigest()


class RoutingDatasetSnapshot(RoutingModel):
    descriptor: RoutingDatasetDescriptor
    queries: tuple[RoutingQuery, ...]
    candidates: tuple[RoutingCandidate, ...]
    outcomes: tuple[RoutingOutcome, ...]
    snapshot_sha256: str
    incomplete: bool = False
    diagnostics: tuple[str, ...] = ()
