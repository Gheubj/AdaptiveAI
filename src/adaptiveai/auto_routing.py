from __future__ import annotations

import re
import time
from dataclasses import dataclass, replace
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from adaptiveai.public import InferenceRequest, ProviderScope, RoutingDiagnostics, RoutingMode


class TaskCategory(StrEnum):
    CODING = "coding"
    MATHEMATICS = "mathematics"
    REASONING = "reasoning"
    WRITING = "writing"
    EXTRACTION = "extraction"
    FACTUAL_QA = "factual_qa"
    DATA_ANALYSIS = "data_analysis"
    TOOL_USE = "tool_use"
    GENERAL = "unknown/general"


class TaskUnderstanding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    category: TaskCategory
    method: str = "deterministic-keywords-v0"
    matched_signals: tuple[str, ...] = ()
    ambiguous: bool = False


class AutoEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence_id: str
    category: TaskCategory
    metric: str
    value: float
    comparability_group: str
    provenance: str
    compatible: bool = True
    revision_known: bool = True


class AutoCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: str
    provider: str
    deployment: str
    model: str
    local: bool = False
    available: bool = True
    capabilities: frozenset[str] = frozenset({"text"})
    context_tokens: int | None = Field(None, ge=1)
    input_per_million: float | None = Field(None, ge=0)
    output_per_million: float | None = Field(None, ge=0)
    currency: str = Field("USD", pattern=r"^[A-Z]{3}$")
    latency_p95_seconds: float | None = Field(None, ge=0)
    evidence: tuple[AutoEvidence, ...] = ()


class ExcludedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: str
    reasons: tuple[str, ...]


class AutoDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: str
    selected_candidate: str | None = None
    selected_provider: str | None = None
    selected_deployment: str | None = None
    selected_model: str | None = None
    mode: str
    task: TaskUnderstanding
    eligible_candidates: tuple[str, ...]
    excluded_candidates: tuple[ExcludedCandidate, ...]
    evidence_ids: tuple[str, ...] = ()
    quality_evidence_available: bool = False
    selection_reason: str
    missing_information: tuple[str, ...] = ()
    estimated_cost: float | None = None
    cost_status: str = "unknown"
    fallback_used: bool = False
    router_overhead_seconds: float


_SIGNALS = {
    TaskCategory.CODING: (r"\b(code|python|javascript|function|debug|sql|api)\b",),
    TaskCategory.MATHEMATICS: (
        r"\b(calculate|equation|integral|derivative|algebra|probability)\b",
        r"\d\s*[+*/^=]\s*\d",
    ),
    TaskCategory.REASONING: (r"\b(reason|logic|deduce|puzzle|step by step)\b",),
    TaskCategory.WRITING: (r"\b(write|rewrite|essay|poem|email|tone|story)\b",),
    TaskCategory.EXTRACTION: (r"\b(extract|parse|entities|fields|json from)\b",),
    TaskCategory.FACTUAL_QA: (r"\b(who|when|where|what is|define|fact)\b",),
    TaskCategory.DATA_ANALYSIS: (r"\b(dataframe|dataset|analy[sz]e|statistics|csv|trend|chart)\b",),
    TaskCategory.TOOL_USE: (r"\b(call tool|use tool|function call|browse|search the web)\b",),
}


def classify_task(text: str) -> TaskUnderstanding:
    normalized = text.lower()
    matched = {
        category: tuple(pattern for pattern in patterns if re.search(pattern, normalized))
        for category, patterns in _SIGNALS.items()
    }
    matched = {category: signals for category, signals in matched.items() if signals}
    if len(matched) != 1:
        return TaskUnderstanding(
            category=TaskCategory.GENERAL,
            matched_signals=tuple(pattern for signals in matched.values() for pattern in signals),
            ambiguous=bool(matched),
        )
    category, signals = next(iter(matched.items()))
    return TaskUnderstanding(category=category, matched_signals=signals)


class InsufficientEvidenceError(ValueError):
    def __init__(self, decision: AutoDecision):
        super().__init__(decision.selection_reason)
        self.decision = decision


@dataclass(frozen=True)
class AutoSelection:
    request: InferenceRequest
    decision: AutoDecision
    diagnostics: RoutingDiagnostics


class AutoRoutingPolicy:
    """Transparent deterministic policy. It is not a learned or validated quality predictor."""

    def __init__(
        self,
        candidates: tuple[AutoCandidate, ...],
        *,
        default_candidate: str | None = None,
        uncertainty_policy: str = "error",
    ):
        self.candidates = {item.candidate_id: item for item in candidates}
        if len(self.candidates) != len(candidates):
            raise ValueError("auto candidate ids must be unique")
        if default_candidate and default_candidate not in self.candidates:
            raise ValueError("auto default candidate is not configured")
        if uncertainty_policy not in {"error", "default"}:
            raise ValueError("uncertainty_policy must be error or default")
        self.default_candidate = default_candidate
        self.uncertainty_policy = uncertainty_policy

    @staticmethod
    def _text(request: InferenceRequest) -> str:
        return "\n".join(item.content for item in request.messages)

    @staticmethod
    def _cost(candidate: AutoCandidate, request: InferenceRequest) -> float | None:
        if candidate.input_per_million is None or candidate.output_per_million is None:
            return None
        chars = sum(len(item.content) + len(item.role) + 4 for item in request.messages)
        input_tokens = max(1, (chars + 2) // 3)
        return (
            input_tokens * candidate.input_per_million
            + request.max_tokens * candidate.output_per_million
        ) / 1_000_000

    def _exclude(self, candidate: AutoCandidate, request: InferenceRequest) -> tuple[str, ...]:
        reasons: list[str] = []
        if not candidate.available:
            reasons.append("UNAVAILABLE")
        if request.local_only and not candidate.local:
            reasons.append("LOCAL_ONLY")
        if request.provider_scope == ProviderScope.LOCAL and not candidate.local:
            reasons.append("PROVIDER_SCOPE")
        if request.provider_scope == ProviderScope.CLOUD and candidate.local:
            reasons.append("PROVIDER_SCOPE")
        if request.provider_allowlist and candidate.provider not in request.provider_allowlist:
            reasons.append("PROVIDER_NOT_ALLOWED")
        if request.provider and candidate.provider != request.provider:
            reasons.append("PROVIDER_NOT_ALLOWED")
        expected_currency = request.cost_currency or "USD"
        if not candidate.local and candidate.currency != expected_currency:
            reasons.append("CURRENCY_MISMATCH")
        if request.required_capabilities - candidate.capabilities:
            reasons.append("REQUIRED_CAPABILITY_UNKNOWN_OR_UNSUPPORTED")
        if request.minimum_context_tokens is not None:
            if candidate.context_tokens is None:
                reasons.append("CONTEXT_UNKNOWN")
            elif candidate.context_tokens < request.minimum_context_tokens:
                reasons.append("CONTEXT_TOO_SMALL")
        cost = self._cost(candidate, request)
        if request.strict_budget and cost is None and not candidate.local:
            reasons.append("PRICING_UNKNOWN")
        if request.max_estimated_cost is not None and cost is not None:
            if cost > request.max_estimated_cost:
                reasons.append("REQUEST_BUDGET_EXCEEDED")
        return tuple(reasons)

    def explain(self, request: InferenceRequest) -> AutoDecision:
        started = time.perf_counter()
        task = classify_task(self._text(request))
        eligible: list[AutoCandidate] = []
        excluded: list[ExcludedCandidate] = []
        for candidate in self.candidates.values():
            reasons = self._exclude(candidate, request)
            if reasons:
                excluded.append(
                    ExcludedCandidate(candidate_id=candidate.candidate_id, reasons=reasons)
                )
            else:
                eligible.append(candidate)
        if request.routing_mode == RoutingMode.MANUAL:
            eligible = [item for item in eligible if item.model == request.model]
        if not eligible:
            return self._decision(
                started,
                request,
                task,
                eligible,
                excluded,
                None,
                "NO_ELIGIBLE_CANDIDATE",
                ("no candidate satisfies hard constraints",),
            )
        if request.routing_mode == RoutingMode.ECONOMY:
            priced = [(self._cost(item, request), item) for item in eligible]
            known = [(cost, item) for cost, item in priced if cost is not None]
            if known:
                cost, selected = min(known, key=lambda row: (row[0], row[1].candidate_id))
                return self._decision(
                    started,
                    request,
                    task,
                    eligible,
                    excluded,
                    selected,
                    "lowest known preflight cost",
                    (),
                    estimated_cost=cost,
                )
            return self._decision(
                started,
                request,
                task,
                eligible,
                excluded,
                None,
                "INSUFFICIENT_EVIDENCE",
                ("all eligible prices are unknown",),
            )
        if request.routing_mode == RoutingMode.MANUAL:
            if len(eligible) == 1:
                return self._decision(
                    started,
                    request,
                    task,
                    eligible,
                    excluded,
                    eligible[0],
                    "explicit manual selection",
                    (),
                )
            return self._decision(
                started,
                request,
                task,
                eligible,
                excluded,
                None,
                "INSUFFICIENT_EVIDENCE",
                ("manual selection did not resolve exactly one candidate",),
            )
        if len(eligible) == 1 and eligible[0].local:
            return self._decision(
                started,
                request,
                task,
                eligible,
                excluded,
                eligible[0],
                "only eligible local candidate after hard constraints",
                ("comparative quality evidence not required for a constrained singleton",),
            )

        groups: dict[str, list[tuple[float, AutoCandidate, AutoEvidence]]] = {}
        for candidate in eligible:
            for evidence in candidate.evidence:
                if (
                    evidence.compatible
                    and evidence.revision_known
                    and evidence.category == task.category
                ):
                    groups.setdefault(evidence.comparability_group, []).append(
                        (evidence.value, candidate, evidence)
                    )
        comparable = [
            rows for rows in groups.values() if len({row[1].candidate_id for row in rows}) >= 2
        ]
        if len(comparable) == 1:
            rows = comparable[0]
            value, selected, _ = max(rows, key=lambda row: (row[0], row[1].candidate_id))
            evidence_ids = tuple(sorted(row[2].evidence_id for row in rows))
            return self._decision(
                started,
                request,
                task,
                eligible,
                excluded,
                selected,
                f"highest compatible {rows[0][2].metric} in one comparison group ({value:g})",
                (),
                evidence_ids=evidence_ids,
                quality=True,
                estimated_cost=self._cost(selected, request),
            )
        if self.uncertainty_policy == "default" and self.default_candidate:
            selected = next(
                (item for item in eligible if item.candidate_id == self.default_candidate), None
            )
            if selected:
                return self._decision(
                    started,
                    request,
                    task,
                    eligible,
                    excluded,
                    selected,
                    "user-configured default under insufficient comparative evidence",
                    ("no single compatible comparative evidence group",),
                    estimated_cost=self._cost(selected, request),
                )
        return self._decision(
            started,
            request,
            task,
            eligible,
            excluded,
            None,
            "INSUFFICIENT_EVIDENCE",
            ("no single compatible comparative evidence group",),
        )

    def _decision(
        self,
        started,
        request,
        task,
        eligible,
        excluded,
        selected,
        reason,
        missing,
        *,
        evidence_ids=(),
        quality=False,
        estimated_cost=None,
    ):
        return AutoDecision(
            status="SELECTED" if selected else reason,
            selected_candidate=selected.candidate_id if selected else None,
            selected_provider=selected.provider if selected else None,
            selected_deployment=selected.deployment if selected else None,
            selected_model=selected.model if selected else None,
            mode=request.routing_mode.value,
            task=task,
            eligible_candidates=tuple(item.candidate_id for item in eligible),
            excluded_candidates=tuple(excluded),
            evidence_ids=evidence_ids,
            quality_evidence_available=quality,
            selection_reason=reason,
            missing_information=missing,
            estimated_cost=estimated_cost,
            cost_status="known_estimate" if estimated_cost is not None else "unknown",
            router_overhead_seconds=time.perf_counter() - started,
        )

    def select(self, request: InferenceRequest) -> AutoSelection:
        decision = self.explain(request)
        if decision.status != "SELECTED":
            raise InsufficientEvidenceError(decision)
        candidate = self.candidates[decision.selected_candidate]
        scope = ProviderScope.LOCAL if candidate.local else ProviderScope.CLOUD
        resolved = replace(
            request,
            model=candidate.model,
            provider=candidate.provider,
            provider_scope=scope,
            local_only=candidate.local,
        )
        diagnostics = RoutingDiagnostics(
            candidate.model,
            request.routing_mode.value,
            decision.selection_reason,
            tuple(item.model for item in self.candidates.values()),
            experimental=True,
            constraints={"provider_scope": scope.value, "eligibility_first": True},
            provider=candidate.provider,
            estimated_cost=decision.estimated_cost,
            usage_source="preflight",
            explanation=decision.model_dump(mode="json"),
        )
        return AutoSelection(resolved, decision, diagnostics)
