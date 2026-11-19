from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from adaptiveai.identity import EvaluationConfiguration
from adaptiveai.permissions import SourcePermissions
from adaptiveai.routing_supervision import (
    RoutingCandidate,
    RoutingDatasetDescriptor,
    RoutingDatasetSnapshot,
    RoutingOutcome,
    RoutingQuery,
    SubjectKind,
)


class RoutingIngestionLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    max_queries: int = Field(1000, ge=1, le=100_000)
    max_candidates: int = Field(128, ge=1, le=1000)
    max_outcomes: int = Field(20_000, ge=1, le=1_000_000)
    max_bytes: int = Field(10_000_000, ge=1024, le=1_000_000_000)


class RoutingDatasetAdapter(ABC):
    descriptor: RoutingDatasetDescriptor

    @abstractmethod
    def discover_splits(self) -> tuple[str, ...]: ...

    @abstractmethod
    def ingest_bytes(
        self, raw: bytes, limits: RoutingIngestionLimits
    ) -> RoutingDatasetSnapshot: ...


class FixtureRoutingDatasetAdapter(RoutingDatasetAdapter):
    def __init__(self, permissions: SourcePermissions):
        self.descriptor = RoutingDatasetDescriptor(
            dataset_id="adaptiveai/synthetic-routing-fixture",
            source_revision="fixture-v1",
            adapter_version="1.0",
            permissions=permissions,
            available_splits=("train", "validation", "test"),
            subject_kind=SubjectKind.MODEL,
        )

    def discover_splits(self) -> tuple[str, ...]:
        return self.descriptor.available_splits

    def ingest_bytes(self, raw: bytes, limits: RoutingIngestionLimits) -> RoutingDatasetSnapshot:
        if len(raw) > limits.max_bytes:
            raise ValueError("routing snapshot exceeds byte limit")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("invalid routing snapshot JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("routing snapshot must be an object")
        diagnostics: list[str] = []
        try:
            candidates = tuple(
                RoutingCandidate.model_validate(item)
                for item in payload.get("candidates", [])[: limits.max_candidates]
            )
            queries = tuple(
                RoutingQuery.model_validate(item)
                for item in payload.get("queries", [])[: limits.max_queries]
            )
        except ValidationError as error:
            raise ValueError(f"invalid routing identity/query schema: {error}") from error
        candidate_ids = {item.candidate_id for item in candidates}
        query_ids = {item.query_id for item in queries}
        outcomes: list[RoutingOutcome] = []
        for index, item in enumerate(payload.get("outcomes", [])[: limits.max_outcomes]):
            try:
                outcome = RoutingOutcome.model_validate(item)
                if outcome.query_id not in query_ids or outcome.candidate_id not in candidate_ids:
                    raise ValueError("outcome references an unknown query or candidate")
                outcomes.append(outcome)
            except (ValidationError, ValueError) as error:
                diagnostics.append(f"outcome[{index}]: {error}")
        incomplete = (
            len(payload.get("queries", [])) > len(queries)
            or len(payload.get("candidates", [])) > len(candidates)
            or len(payload.get("outcomes", [])) > len(outcomes) + len(diagnostics)
            or bool(diagnostics)
        )
        return RoutingDatasetSnapshot(
            descriptor=self.descriptor,
            queries=queries,
            candidates=candidates,
            outcomes=tuple(outcomes),
            snapshot_sha256=hashlib.sha256(raw).hexdigest(),
            incomplete=incomplete,
            diagnostics=tuple(diagnostics),
        )


def fixture_outcome(
    *,
    query_id: str,
    candidate_id: str,
    score: float,
    permissions: SourcePermissions,
    cost: float | None = None,
    latency: float | None = None,
) -> RoutingOutcome:
    missing = ["response", "input_tokens", "output_tokens"]
    if cost is None:
        missing.extend(("historical_cost_usd", "price_source"))
    if latency is None:
        missing.append("latency_seconds")
    return RoutingOutcome(
        query_id=query_id,
        candidate_id=candidate_id,
        score=score,
        metric_id="correct",
        metric_units="binary",
        metric_scale="0..1",
        evaluation=EvaluationConfiguration(harness="fixture", harness_version="1"),
        latency_seconds=latency,
        historical_cost_usd=cost,
        price_source="fixture historical price" if cost is not None else None,
        provenance=("synthetic-fixture",),
        permissions=permissions,
        missing=tuple(missing),
    )
