from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from adaptiveai.benchmarks import AdapterDescriptor, FixtureBenchmarkAdapter
from adaptiveai.capabilities import (
    CapabilityProfile,
    CapabilityValue,
    SupportState,
    validate_profile_evidence,
)
from adaptiveai.eligibility import (
    DeploymentState,
    EligibilityConstraints,
    EligibilityStatus,
    ReasonCode,
    evaluate_eligibility,
)
from adaptiveai.evidence import (
    EvidenceRecord,
    EvidenceType,
    MissingValue,
    Reliability,
    SystemKind,
    compare_evidence,
    index_evidence,
)
from adaptiveai.identity import (
    DeploymentIdentity,
    EvaluationConfiguration,
    EvaluationSubject,
    ModelFamily,
    ModelIdentity,
    ModelRevision,
    ProviderAlias,
    ProviderIdentity,
    RevisionStatus,
)
from adaptiveai.intelligence import CompatibilityRoutingAdapter
from adaptiveai.permissions import PermissionState, SourcePermissions, evaluate_export
from adaptiveai.public import ChatMessage, InferenceRequest, RoutingMode
from adaptiveai.routing_engine import ModelProfile, RoutingEngine

NOW = datetime(2026, 11, 18, tzinfo=UTC)


def identity(revision: str = "abc123") -> ModelIdentity:
    return ModelIdentity(
        family=ModelFamily(namespace="Example Org", family="Example Family"),
        model="Model 1B",
        revision=ModelRevision(revision=revision, status=RevisionStatus.VERIFIED, source="fixture"),
        quantization="Q4_K_M",
    )


def subject(revision: str = "abc123", harness_version: str = "1") -> EvaluationSubject:
    return EvaluationSubject(
        model=identity(revision),
        configuration=EvaluationConfiguration(
            harness="fixture-harness", harness_version=harness_version, parameters={"seed": 3407}
        ),
    )


def permissions(redistribution=PermissionState.UNKNOWN) -> SourcePermissions:
    return SourcePermissions(
        metadata_access=PermissionState.ALLOWED,
        local_ingestion=PermissionState.ALLOWED,
        local_analysis=PermissionState.ALLOWED,
        derived_use=PermissionState.ALLOWED,
        redistribution=redistribution,
        attribution_required=False,
        commercial_use=PermissionState.UNKNOWN,
    )


def evidence(**updates) -> EvidenceRecord:
    values = dict(
        evidence_type=EvidenceType.LOCAL_EVALUATION,
        source_id="fixture",
        source_version="1",
        retrieved_at=NOW,
        subject=subject(),
        system_kind=SystemKind.BASE_MODEL,
        benchmark="tiny-eval",
        benchmark_version="1",
        task_distribution="held-out-v1",
        method="exact-match",
        metric="accuracy",
        value=0.5,
        units="fraction",
        scale="0..1",
        sample_size=10,
        provenance=("fixture.json",),
        reliability=Reliability.REPRODUCED,
        permissions=permissions(),
    )
    values.update(updates)
    return EvidenceRecord(**values)


def deployment(model: ModelIdentity | None = None) -> DeploymentIdentity:
    return DeploymentIdentity(
        deployment_id="local-fixture",
        provider=ProviderIdentity(provider_id="local"),
        model=model or identity(),
        endpoint_kind="llama.cpp",
    )


def profile(**updates) -> CapabilityProfile:
    values = dict(
        profile_id="example-model-profile",
        profile_version=1,
        model=identity(),
        created_at=NOW,
        input_modalities={"text": CapabilityValue(state=SupportState.SUPPORTED)},
        output_modalities={"text": CapabilityValue(state=SupportState.SUPPORTED)},
        tool_use=CapabilityValue(state=SupportState.UNKNOWN),
        structured_output=CapabilityValue(state=SupportState.UNKNOWN),
        context_window_tokens=4096,
    )
    values.update(updates)
    return CapabilityProfile(**values)


def test_identity_separates_family_revision_quantization_provider_and_alias_time():
    model = identity()
    assert model.family.family_id == "example-org/example-family"
    assert model.canonical_id.endswith("@abc123#q4_k_m")
    provider = ProviderIdentity(provider_id="Example Cloud")
    alias = ProviderAlias(provider=provider, alias="latest", model=model, valid_from=NOW)
    assert alias.provider.canonical_id == "example-cloud"
    assert alias.alias == "latest"
    with pytest.raises(ValidationError, match="valid_until"):
        ProviderAlias(provider=provider, alias="bad", model=model, valid_from=NOW, valid_until=NOW)


def test_unknown_revision_and_evaluation_fingerprint_are_explicit_and_deterministic():
    unknown = ModelIdentity(family=ModelFamily(namespace="x", family="y"), model="z")
    assert "revision-unknown" in unknown.canonical_id
    assert subject().configuration.fingerprint == subject().configuration.fingerprint
    with pytest.raises(ValidationError, match="requires a revision"):
        ModelRevision(status=RevisionStatus.VERIFIED)


def test_evidence_missingness_identity_deduplication_and_comparability():
    record = evidence()
    assert record.evidence_id == evidence().evidence_id
    with pytest.raises(ValueError, match="duplicate evidence"):
        index_evidence((record, record))
    missing_value = evidence(
        value=None, missing=(MissingValue(field="value", reason="not reported"),)
    )
    assert missing_value.value is None
    with pytest.raises(ValidationError, match="not declared"):
        evidence(value=None)
    assert compare_evidence(record, evidence()).comparable
    diagnostic = compare_evidence(
        record,
        evidence(subject=subject(revision="def456", harness_version="2"), scale="percent"),
    )
    assert not diagnostic.comparable
    assert {"model_revision", "harness_version", "evaluation_configuration", "scale"} <= set(
        diagnostic.mismatches
    )


def test_permission_ledger_denies_unknown_and_requires_attribution():
    assert not evaluate_export(permissions()).allowed
    allowed = permissions(PermissionState.ALLOWED)
    assert evaluate_export(allowed).allowed
    required = allowed.model_copy(update={"attribution_required": True, "attribution_text": None})
    assert evaluate_export(required).reasons == ("required_attribution_missing",)


def test_profile_preserves_unknowns_and_validates_evidence_ownership_and_comparability():
    record = evidence()
    attached = profile(benchmark_evidence_ids=(record.evidence_id,))
    assert validate_profile_evidence(attached, {record.evidence_id: record}) == ()
    other = evidence(subject=subject(revision="different"))
    with pytest.raises(ValueError, match="another model"):
        validate_profile_evidence(
            profile(benchmark_evidence_ids=(other.evidence_id,)), {other.evidence_id: other}
        )
    with pytest.raises(ValidationError, match="must be explicit"):
        profile(context_window_tokens=None)


def test_eligibility_returns_eligible_ineligible_and_unknown_with_reasons():
    state = DeploymentState(deployment=deployment(), local=True, available=True, memory_bytes=100)
    constraints = EligibilityConstraints(
        local_only=True,
        required_input_modalities=frozenset({"text"}),
        minimum_context_tokens=2048,
        available_memory_bytes=200,
    )
    assert evaluate_eligibility(profile(), state, constraints).status == EligibilityStatus.ELIGIBLE
    rejected = evaluate_eligibility(
        profile(), state.model_copy(update={"local": False}), constraints
    )
    assert rejected.status == EligibilityStatus.INELIGIBLE
    assert ReasonCode.LOCAL_ONLY in {reason.code for reason in rejected.reasons}
    uncertain = evaluate_eligibility(
        profile(context_window_tokens=None, missing_information=("context_window_tokens",)),
        state.model_copy(update={"available": None, "memory_bytes": None}),
        constraints.model_copy(update={"require_tools": True}),
    )
    assert uncertain.status == EligibilityStatus.UNKNOWN
    expected = {
        ReasonCode.AVAILABILITY_UNKNOWN,
        ReasonCode.TOOLS_UNKNOWN,
        ReasonCode.CONTEXT_UNKNOWN,
    }
    assert expected <= {reason.code for reason in uncertain.reasons}


def test_fixture_adapter_validates_and_normalizes_without_network():
    adapter = FixtureBenchmarkAdapter(
        AdapterDescriptor(
            adapter_id="fixture",
            adapter_version="1",
            source_id="permitted-fixture",
            source_version="2026-11-18",
            permissions=permissions(PermissionState.ALLOWED),
        )
    )
    payload = [
        {
            "benchmark": "tiny",
            "benchmark_version": "1",
            "task_distribution": "fixture",
            "metric": "accuracy",
            "value": 0.5,
            "units": "fraction",
            "scale": "0..1",
            "sample_size": 2,
            "retrieved_at": NOW.isoformat(),
        }
    ]
    records = adapter.normalize(payload, subject())
    assert records[0].evidence_type == EvidenceType.EXTERNAL_AGGREGATE
    with pytest.raises(ValueError, match="non-empty"):
        adapter.normalize([], subject())


def test_v010_compatibility_adapter_preserves_frozen_routing_result_and_error():
    profiles = (
        ModelProfile("fast", estimated_quality=0.4, predicted_p95_latency_seconds=0.2),
        ModelProfile("strong", estimated_quality=0.8, predicted_p95_latency_seconds=1.0),
    )
    legacy = RoutingEngine(profiles)
    adapter = CompatibilityRoutingAdapter(legacy)
    request = InferenceRequest(
        messages=(ChatMessage("user", "frozen fixture"),), routing_mode=RoutingMode.BALANCED
    )
    assert adapter.select(request) == legacy.select(request)
    with pytest.raises(ValueError, match="Unknown model"):
        adapter.select(replace(request, model="missing"))
