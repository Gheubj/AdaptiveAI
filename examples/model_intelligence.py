"""Offline Phase 6A example: identities, evidence, eligibility, and safe export."""

from datetime import UTC, datetime

from adaptiveai.capabilities import CapabilityProfile, CapabilityValue, SupportState
from adaptiveai.eligibility import DeploymentState, EligibilityConstraints, evaluate_eligibility
from adaptiveai.evidence import EvidenceRecord, EvidenceType, Reliability, SystemKind
from adaptiveai.identity import (
    DeploymentIdentity,
    EvaluationConfiguration,
    EvaluationSubject,
    ModelFamily,
    ModelIdentity,
    ModelRevision,
    ProviderIdentity,
    RevisionStatus,
)
from adaptiveai.intelligence import CompatibilityRoutingAdapter
from adaptiveai.permissions import PermissionState, SourcePermissions, evaluate_export
from adaptiveai.public import ChatMessage, InferenceRequest, RoutingMode
from adaptiveai.routing_engine import ModelProfile, RoutingEngine

model = ModelIdentity(
    family=ModelFamily(namespace="example", family="small-models"),
    model="example-1b",
    revision=ModelRevision(revision="abc123", status=RevisionStatus.VERIFIED),
    quantization="Q4_K_M",
)
deployment = DeploymentIdentity(
    deployment_id="laptop-cpu",
    provider=ProviderIdentity(provider_id="local"),
    model=model,
)
profile = CapabilityProfile(
    profile_id="example-1b-local",
    profile_version=1,
    model=model,
    created_at=datetime.now(UTC),
    input_modalities={"text": CapabilityValue(state=SupportState.SUPPORTED)},
    output_modalities={"text": CapabilityValue(state=SupportState.SUPPORTED)},
    context_window_tokens=None,
    missing_information=("context_window_tokens",),
)
source_permissions = SourcePermissions(
    local_ingestion=PermissionState.ALLOWED,
    local_analysis=PermissionState.ALLOWED,
    redistribution=PermissionState.UNKNOWN,
    attribution_required=None,
)
record = EvidenceRecord(
    evidence_type=EvidenceType.LOCAL_EVALUATION,
    source_id="synthetic-example",
    source_version="1",
    retrieved_at=datetime.now(UTC),
    subject=EvaluationSubject(
        model=model,
        deployment=deployment,
        configuration=EvaluationConfiguration(harness="example", harness_version="1"),
    ),
    system_kind=SystemKind.PROVIDER_DEPLOYMENT,
    benchmark="synthetic-smoke",
    benchmark_version="1",
    task_distribution="synthetic",
    method="exact-match",
    metric="accuracy",
    value=0.5,
    units="fraction",
    scale="0..1",
    sample_size=2,
    reliability=Reliability.REPRODUCED,
    permissions=source_permissions,
)
decision = evaluate_eligibility(
    profile,
    DeploymentState(deployment=deployment, local=True, available=True),
    EligibilityConstraints(local_only=True, minimum_context_tokens=4096),
)
print(model.canonical_id)
print(decision.model_dump_json(indent=2))  # UNKNOWN, never invented from absent metadata
print(record.evidence_id, evaluate_export(source_permissions).model_dump())  # export denied

# A known policy violation is INELIGIBLE, even if other metadata is unknown.
rejected = evaluate_eligibility(
    profile,
    DeploymentState(deployment=deployment, local=False, available=True),
    EligibilityConstraints(local_only=True),
)
print(rejected.model_dump_json(indent=2))

# Existing v0.1.0 requests keep the exact legacy routing behavior through the adapter.
legacy = RoutingEngine((ModelProfile("example", estimated_quality=0.5),))
compatibility = CompatibilityRoutingAdapter(legacy)
request = InferenceRequest(
    messages=(ChatMessage("user", "hello"),),
    model="example",
    routing_mode=RoutingMode.QUALITY,
)
print(compatibility.select(request))
