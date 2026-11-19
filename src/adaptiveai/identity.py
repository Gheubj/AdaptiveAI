from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IdentityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RevisionStatus(StrEnum):
    VERIFIED = "verified"
    DECLARED = "declared"
    UNKNOWN = "unknown"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower()).strip("-")
    if not normalized:
        raise ValueError("identifier must contain alphanumeric characters")
    return normalized


class ModelFamily(IdentityModel):
    namespace: str
    family: str

    @property
    def family_id(self) -> str:
        return f"{_slug(self.namespace)}/{_slug(self.family)}"


class ModelRevision(IdentityModel):
    revision: str | None = None
    status: RevisionStatus = RevisionStatus.UNKNOWN
    source: str | None = None

    @model_validator(mode="after")
    def revision_matches_status(self) -> ModelRevision:
        if self.status != RevisionStatus.UNKNOWN and not self.revision:
            raise ValueError("non-unknown revision status requires a revision")
        if self.status == RevisionStatus.UNKNOWN and self.revision is not None:
            raise ValueError("unknown revision status cannot carry a revision")
        return self


class ModelIdentity(IdentityModel):
    family: ModelFamily
    model: str
    revision: ModelRevision = Field(default_factory=ModelRevision)
    quantization: str | None = None

    @property
    def canonical_id(self) -> str:
        base = f"{self.family.family_id}/{_slug(self.model)}"
        revision = self.revision.revision or "revision-unknown"
        quantization = _slug(self.quantization) if self.quantization else "quantization-unknown"
        return f"{base}@{_slug(revision)}#{quantization}"


class ProviderIdentity(IdentityModel):
    provider_id: str
    display_name: str | None = None

    @property
    def canonical_id(self) -> str:
        return _slug(self.provider_id)


class ProviderAlias(IdentityModel):
    provider: ProviderIdentity
    alias: str
    model: ModelIdentity
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @model_validator(mode="after")
    def valid_interval(self) -> ProviderAlias:
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")
        return self


class DeploymentIdentity(IdentityModel):
    deployment_id: str
    provider: ProviderIdentity
    model: ModelIdentity
    region: str | None = None
    endpoint_kind: str | None = None

    @property
    def canonical_id(self) -> str:
        return f"{self.provider.canonical_id}/{_slug(self.deployment_id)}"


class EvaluationConfiguration(IdentityModel):
    harness: str
    harness_version: str
    parameters: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class EvaluationSubject(IdentityModel):
    model: ModelIdentity
    deployment: DeploymentIdentity | None = None
    configuration: EvaluationConfiguration

    @model_validator(mode="after")
    def deployment_matches_model(self) -> EvaluationSubject:
        if self.deployment and self.deployment.model != self.model:
            raise ValueError("deployment and evaluation model identities differ")
        return self
