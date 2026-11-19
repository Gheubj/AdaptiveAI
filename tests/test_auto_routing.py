import pytest

from adaptiveai.auto_routing import (
    AutoCandidate,
    AutoEvidence,
    AutoRoutingPolicy,
    InsufficientEvidenceError,
    TaskCategory,
    classify_task,
)
from adaptiveai.public import ChatMessage, InferenceRequest, ProviderScope, RoutingMode


def evidence(candidate, category, value, group="synthetic-v1", **updates):
    row = {
        "evidence_id": f"synthetic-{candidate}-{category}-{value}",
        "category": category,
        "metric": "synthetic_accuracy",
        "value": value,
        "comparability_group": group,
        "provenance": "explicit synthetic Phase 7 fixture",
    }
    row.update(updates)
    return AutoEvidence(**row)


def candidates():
    return (
        AutoCandidate(
            candidate_id="local-code",
            provider="local",
            deployment="laptop",
            model="local-code",
            local=True,
            capabilities=frozenset({"text", "code"}),
            context_tokens=4096,
            latency_p95_seconds=0.2,
            evidence=(evidence("local", TaskCategory.CODING, 0.7),),
        ),
        AutoCandidate(
            candidate_id="cloud-code",
            provider="mock",
            deployment="test",
            model="cloud-code",
            capabilities=frozenset({"text", "code", "tools"}),
            context_tokens=8192,
            input_per_million=1,
            output_per_million=2,
            latency_p95_seconds=0.1,
            evidence=(evidence("cloud", TaskCategory.CODING, 0.8),),
        ),
        AutoCandidate(
            candidate_id="cloud-unknown",
            provider="mock",
            deployment="test-unknown",
            model="cloud-unknown",
            capabilities=frozenset({"text"}),
            context_tokens=None,
            input_per_million=None,
            output_per_million=None,
            evidence=(
                evidence(
                    "unknown",
                    TaskCategory.CODING,
                    0.99,
                    revision_known=False,
                ),
            ),
        ),
    )


def request(text="Debug Python code", **updates):
    values = {
        "messages": (ChatMessage("user", text),),
        "routing_mode": RoutingMode.AUTO,
        "provider_scope": ProviderScope.HYBRID,
        "local_only": False,
        "strict_budget": False,
    }
    values.update(updates)
    return InferenceRequest(**values)


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("Debug this Python function", TaskCategory.CODING),
        ("Calculate the integral", TaskCategory.MATHEMATICS),
        ("Write a short email", TaskCategory.WRITING),
        ("Extract fields as JSON", TaskCategory.EXTRACTION),
        ("Analyze this CSV dataset", TaskCategory.DATA_ANALYSIS),
        ("Hello there", TaskCategory.GENERAL),
    ],
)
def test_task_understanding(text, category):
    result = classify_task(text)
    assert result.category == category
    assert result.method == "deterministic-keywords-v0"


def test_ambiguous_task_abstains_to_general():
    result = classify_task("Write Python code and an email")
    assert result.category == TaskCategory.GENERAL
    assert result.ambiguous


def test_auto_uses_only_comparable_known_revision_evidence():
    result = AutoRoutingPolicy(candidates()).select(request())
    assert result.decision.selected_candidate == "cloud-code"
    assert result.decision.quality_evidence_available
    assert "synthetic-cloud" in " ".join(result.decision.evidence_ids)
    assert result.diagnostics.explanation["task"]["category"] == "coding"
    serialized = result.decision.model_dump_json()
    assert "Debug Python code" not in serialized
    assert "api_key" not in serialized.lower()


def test_constraints_run_before_ranking_and_local_only_cannot_be_overridden():
    decision = AutoRoutingPolicy(candidates()).explain(
        request(local_only=True, provider_scope=ProviderScope.HYBRID)
    )
    assert decision.selected_candidate == "local-code"
    excluded = {item.candidate_id: item.reasons for item in decision.excluded_candidates}
    assert "LOCAL_ONLY" in excluded["cloud-code"]


def test_capability_context_provider_and_budget_constraints():
    decision = AutoRoutingPolicy(candidates()).explain(
        request(
            required_capabilities=frozenset({"tools"}),
            minimum_context_tokens=6000,
            provider_allowlist=("mock",),
            max_estimated_cost=0,
        )
    )
    assert decision.status == "NO_ELIGIBLE_CANDIDATE"
    assert all(item.reasons for item in decision.excluded_candidates)


def test_missing_and_conflicting_evidence_is_explicit():
    router = AutoRoutingPolicy(candidates())
    decision = router.explain(request("Tell me something"))
    assert decision.status == "INSUFFICIENT_EVIDENCE"
    with pytest.raises(InsufficientEvidenceError):
        router.select(request("Tell me something"))
    conflicting = tuple(
        item.model_copy(
            update={
                "evidence": (
                    evidence(
                        item.candidate_id,
                        TaskCategory.CODING,
                        0.5,
                        group=item.candidate_id,
                    ),
                )
            }
        )
        for item in candidates()[:2]
    )
    assert AutoRoutingPolicy(conflicting).explain(request()).status == "INSUFFICIENT_EVIDENCE"


def test_default_and_economy_policies_are_predictable():
    router = AutoRoutingPolicy(
        candidates(), default_candidate="local-code", uncertainty_policy="default"
    )
    assert router.explain(request("General request")).selected_candidate == "local-code"
    economy = router.explain(request(routing_mode=RoutingMode.ECONOMY))
    assert economy.selected_candidate == "cloud-code"
    assert economy.cost_status == "known_estimate"


def test_manual_selection_and_determinism():
    router = AutoRoutingPolicy(candidates())
    manual = request(routing_mode=RoutingMode.MANUAL, model="local-code")
    assert router.select(manual).decision.selected_candidate == "local-code"
    outputs = [router.explain(request()).model_dump_json() for _ in range(3)]
    # Timing is diagnostic and expected to differ; all policy outputs remain stable.
    stripped = [item.split('"router_overhead_seconds":')[0] for item in outputs]
    assert len(set(stripped)) == 1


def test_unknown_revision_is_not_quality_evidence():
    only_unknown = (candidates()[2],)
    decision = AutoRoutingPolicy(only_unknown).explain(request())
    assert not decision.quality_evidence_available
    assert decision.status == "INSUFFICIENT_EVIDENCE"
