from __future__ import annotations

from adaptiveai.eligibility import (
    DeploymentState,
    EligibilityConstraints,
    EligibilityDecision,
    evaluate_eligibility,
)
from adaptiveai.public import InferenceRequest, RoutingDiagnostics
from adaptiveai.routing_engine import RoutingEngine


class CompatibilityRoutingAdapter:
    """Phase 6A boundary that preserves the v0.1.0 routing contract exactly."""

    def __init__(self, legacy: RoutingEngine):
        self.legacy = legacy

    def select(self, request: InferenceRequest) -> RoutingDiagnostics:
        return self.legacy.select(request)

    def eligible(self, request: InferenceRequest):
        return self.legacy.eligible(request)


def check_deployment(
    profile, deployment: DeploymentState, constraints: EligibilityConstraints
) -> EligibilityDecision:
    return evaluate_eligibility(profile, deployment, constraints)
