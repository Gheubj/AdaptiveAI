from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from adaptiveai.permissions import PermissionState, SourcePermissions, evaluate_export
from adaptiveai.routing_data_analysis import (
    analyze_binary_headroom,
    analyze_oracle_cost,
    audit_leakage,
    audit_matrix,
    deterministic_query_sample,
)
from adaptiveai.routing_dataset_adapter import (
    FixtureRoutingDatasetAdapter,
    RoutingIngestionLimits,
    fixture_outcome,
)
from adaptiveai.routing_preregistration import (
    BaselineDataAvailability,
    BaselineName,
    baseline_eligibility,
)
from adaptiveai.routing_supervision import (
    DataRole,
    RoutingCandidate,
    RoutingOutcome,
    RoutingQuery,
)


def permissions() -> SourcePermissions:
    return SourcePermissions(
        metadata_access=PermissionState.ALLOWED,
        local_ingestion=PermissionState.ALLOWED,
        local_analysis=PermissionState.ALLOWED,
        derived_use=PermissionState.ALLOWED,
        redistribution=PermissionState.PROHIBITED,
        attribution_required=True,
        attribution_text="Synthetic AdaptiveAI test fixture",
        commercial_use=PermissionState.NOT_APPLICABLE,
    )


def query(query_id: str, split: str = "train", content: str | None = None) -> RoutingQuery:
    role = DataRole.TRAIN if split == "train" else DataRole.EXPLORATORY_TEST
    return RoutingQuery(
        query_id=query_id,
        split=split,
        data_role=role,
        task_family="reasoning",
        task_name="synthetic-binary",
        metric_id="correct",
        metric_units="binary",
        metric_scale="0..1",
        content=content or f"Question {query_id}",
        provenance=("fixture",),
    )


def candidate(candidate_id: str) -> RoutingCandidate:
    return RoutingCandidate(
        candidate_id=candidate_id,
        source_model_id=f"historical/{candidate_id}",
        historical_only=True,
    )


def payload(*, include_cost: bool = True) -> bytes:
    costs = {"a": 0.02, "b": 0.01}
    latencies = {"a": 2.0, "b": 1.0}
    scores = {
        ("q1", "a"): 1.0,
        ("q1", "b"): 0.0,
        ("q2", "a"): 0.0,
        ("q2", "b"): 1.0,
        ("q3", "a"): 1.0,
        ("q3", "b"): 1.0,
    }
    outcomes = [
        fixture_outcome(
            query_id=query_id,
            candidate_id=model_id,
            score=score,
            permissions=permissions(),
            cost=costs[model_id] if include_cost else None,
            latency=latencies[model_id],
        ).model_dump(mode="json")
        for (query_id, model_id), score in scores.items()
    ]
    return json.dumps(
        {
            "queries": [query(item).model_dump(mode="json") for item in ("q1", "q2", "q3")],
            "candidates": [candidate(item).model_dump(mode="json") for item in ("a", "b")],
            "outcomes": outcomes,
        }
    ).encode()


def snapshot(*, include_cost: bool = True):
    return FixtureRoutingDatasetAdapter(permissions()).ingest_bytes(
        payload(include_cost=include_cost), RoutingIngestionLimits()
    )


def test_evidence_classes_remain_distinct_and_missingness_is_explicit():
    outcome = fixture_outcome(query_id="q", candidate_id="m", score=1, permissions=permissions())
    assert outcome.evidence_class.value == "routing_supervision"
    assert "historical_cost_usd" in outcome.missing
    assert not evaluate_export(outcome.permissions).allowed
    data = outcome.model_dump()
    data["missing"] = ()
    with pytest.raises(ValidationError, match="not declared missing"):
        RoutingOutcome.model_validate(data)


def test_fixture_adapter_preserves_splits_metrics_and_bounds():
    adapter = FixtureRoutingDatasetAdapter(permissions())
    result = adapter.ingest_bytes(payload(), RoutingIngestionLimits(max_queries=2))
    assert adapter.discover_splits() == ("train", "validation", "test")
    assert len(result.queries) == 2
    assert result.incomplete
    assert {item.metric_id for item in result.outcomes} == {"correct"}
    with pytest.raises(ValueError, match="byte limit"):
        adapter.ingest_bytes(payload(), RoutingIngestionLimits(max_bytes=1024))


def test_matrix_missing_duplicates_conflicts_and_incompatible_metrics():
    base = snapshot()
    audit = audit_matrix(base)
    assert audit.expected_pairs == audit.outcome_count == 6
    assert not audit.missing_pairs
    duplicate = base.model_copy(update={"outcomes": base.outcomes + (base.outcomes[0],)})
    assert audit_matrix(duplicate).exact_duplicates == 1
    changed = base.outcomes[0].model_copy(update={"score": 0.5})
    conflict = base.model_copy(update={"outcomes": base.outcomes + (changed,)})
    assert audit_matrix(conflict).conflicting_duplicates == (("q1", "a"),)
    partial = base.model_copy(update={"outcomes": base.outcomes[:-1]})
    assert audit_matrix(partial).missing_pairs == (("q3", "b"),)
    incompatible = base.outcomes[0].model_copy(update={"metric_scale": "0..100"})
    bad_metric = base.model_copy(update={"outcomes": (incompatible,) + base.outcomes[1:]})
    assert len(audit_matrix(bad_metric).incompatible_metric_rows) == 1


def test_deterministic_sampling_and_leakage_roles():
    queries = tuple(query(f"q{index}") for index in range(10))
    first = deterministic_query_sample(queries, maximum=4, seed=7)
    second = deterministic_query_sample(tuple(reversed(queries)), maximum=4, seed=7)
    assert [item.query_id for item in first] == [item.query_id for item in second]
    train = query("train-id", content="Same prompt")
    test = query("test-id", split="test", content=" same   PROMPT ")
    audit = audit_leakage((train, test))
    assert audit.exact_cross_split == (("test-id", "train-id"),)
    assert not audit.confirmatory_valid


def test_headroom_pairwise_latency_cost_and_uncertainty():
    analysis = analyze_binary_headroom(snapshot(), bootstrap_samples=200, seed=11)
    assert analysis.best_single_quality == pytest.approx(2 / 3)
    assert analysis.oracle_quality == 1
    assert analysis.oracle_gain == pytest.approx(1 / 3)
    assert analysis.cheapest_candidate == "b"
    assert analysis.fastest_candidate == "b"
    pair = analysis.pairwise[0]
    assert (pair.left_only_success, pair.right_only_success, pair.both_success) == (1, 1, 1)
    assert analysis.oracle_quality_ci95 == (1.0, 1.0)


def test_cost_analysis_refuses_missing_historical_prices_and_labels_oracle():
    missing = analyze_oracle_cost(snapshot(include_cost=False), quality_floor=0.5)
    assert not missing.feasible
    assert "current prices were not substituted" in missing.limitation
    available = analyze_oracle_cost(snapshot(), quality_floor=0.5)
    assert available.feasible
    assert available.best_fixed_candidate == "b"
    assert "post-hoc oracle" in available.limitation


def test_historical_candidate_is_not_live_deployment_identity():
    historical = candidate("a")
    assert historical.historical_only
    assert historical.model_identity is None
    with pytest.raises(ValidationError, match="must match"):
        RoutingCandidate(
            candidate_id="bad",
            source_model_id="bad",
            exact_revision_known=True,
            historical_only=False,
        )


def test_preregistered_baseline_eligibility_uses_only_available_evidence():
    data = BaselineDataAvailability(
        candidate_count=2,
        matched_quality=True,
        query_text=True,
        task_labels=True,
        historical_cost=False,
        observed_latency=False,
        capability_profiles=False,
    )
    assert baseline_eligibility(BaselineName.TFIDF, data).eligible
    assert not baseline_eligibility(BaselineName.FIXED_CHEAPEST, data).eligible
    assert not baseline_eligibility(BaselineName.FIXED_FASTEST, data).eligible
    assert baseline_eligibility(BaselineName.ORACLE, data).posthoc_only
    conditioned = baseline_eligibility(BaselineName.MODEL_CONDITIONED, data)
    assert conditioned.missing_requirements == ("capability_profiles",)
