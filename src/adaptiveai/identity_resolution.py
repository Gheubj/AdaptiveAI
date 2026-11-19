from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from adaptiveai.identity import ModelIdentity, ProviderAlias


class ResolutionStatus(StrEnum):
    EXACT = "exact"
    VERIFIED_ALIAS = "verified_alias"
    POSSIBLE_ALIAS = "possible_alias"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class IdentityResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_model_id: str
    status: ResolutionStatus
    model: ModelIdentity | None = None
    candidates: tuple[str, ...] = ()
    reason: str


class IdentityResolver:
    def __init__(
        self,
        models: tuple[ModelIdentity, ...] = (),
        aliases: tuple[ProviderAlias, ...] = (),
    ):
        self.models = models
        self.aliases = aliases

    def resolve(self, source_model_id: str) -> IdentityResolution:
        exact = [model for model in self.models if model.canonical_id == source_model_id]
        if len(exact) == 1:
            return IdentityResolution(
                source_model_id=source_model_id,
                status=ResolutionStatus.EXACT,
                model=exact[0],
                reason="source identifier exactly equals canonical identity",
            )
        aliases = [alias.model for alias in self.aliases if alias.alias == source_model_id]
        unique = {model.canonical_id: model for model in aliases}
        if len(unique) == 1:
            return IdentityResolution(
                source_model_id=source_model_id,
                status=ResolutionStatus.VERIFIED_ALIAS,
                model=next(iter(unique.values())),
                reason="matched one registered provider alias",
            )
        if len(unique) > 1:
            return IdentityResolution(
                source_model_id=source_model_id,
                status=ResolutionStatus.AMBIGUOUS,
                candidates=tuple(sorted(unique)),
                reason="provider alias maps to multiple identities",
            )
        return IdentityResolution(
            source_model_id=source_model_id,
            status=ResolutionStatus.UNRESOLVED,
            reason="no exact identity or verified alias; fuzzy matching prohibited",
        )
