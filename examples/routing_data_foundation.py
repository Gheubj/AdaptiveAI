"""Offline-only routing supervision example using synthetic, non-external data."""

import json

from adaptiveai.permissions import PermissionState, SourcePermissions
from adaptiveai.routing_data_analysis import analyze_binary_headroom, audit_matrix
from adaptiveai.routing_dataset_adapter import (
    FixtureRoutingDatasetAdapter,
    RoutingIngestionLimits,
    fixture_outcome,
)
from adaptiveai.routing_supervision import DataRole, RoutingCandidate, RoutingQuery

permissions = SourcePermissions(
    local_ingestion=PermissionState.ALLOWED,
    local_analysis=PermissionState.ALLOWED,
    derived_use=PermissionState.ALLOWED,
    redistribution=PermissionState.PROHIBITED,
    attribution_required=False,
    commercial_use=PermissionState.NOT_APPLICABLE,
)
queries = [
    RoutingQuery(
        query_id=f"q{index}",
        split="train",
        data_role=DataRole.TRAIN,
        task_family="synthetic",
        task_name="binary-demo",
        metric_id="correct",
        metric_units="binary",
        metric_scale="0..1",
        content=f"Synthetic question {index}",
        provenance=("adaptiveai-fixture",),
    )
    for index in range(2)
]
candidates = [
    RoutingCandidate(candidate_id=name, source_model_id=name, historical_only=True)
    for name in ("model-a", "model-b")
]
outcomes = [
    fixture_outcome(
        query_id=query.query_id,
        candidate_id=candidate.candidate_id,
        score=float(
            query.query_id[-1] == candidate.candidate_id[-1].replace("a", "0").replace("b", "1")
        ),
        permissions=permissions,
        cost=0.001,
        latency=0.1,
    )
    for query in queries
    for candidate in candidates
]
payload = json.dumps(
    {
        "queries": [item.model_dump(mode="json") for item in queries],
        "candidates": [item.model_dump(mode="json") for item in candidates],
        "outcomes": [item.model_dump(mode="json") for item in outcomes],
    }
).encode()
snapshot = FixtureRoutingDatasetAdapter(permissions).ingest_bytes(payload, RoutingIngestionLimits())
print(audit_matrix(snapshot).model_dump_json(indent=2))
print(analyze_binary_headroom(snapshot, bootstrap_samples=100).model_dump_json(indent=2))
