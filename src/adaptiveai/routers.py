from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


@dataclass(frozen=True)
class RoutingRequest:
    query_id: str
    text: str
    allowed_models: tuple[str, ...]
    features: dict[str, Any] = field(default_factory=dict)
    max_expected_cost: float | None = None


@dataclass(frozen=True)
class RoutingDecision:
    model_id: str
    diagnostics: dict[str, Any] = field(default_factory=dict)


class Router(ABC):
    """Deployable interface. Current-query outcomes are intentionally absent."""

    @abstractmethod
    def route(self, request: RoutingRequest) -> RoutingDecision: ...


class RandomRouter(Router):
    def __init__(self, seed: int) -> None:
        self.rng = np.random.default_rng(seed)
        self.seed = seed

    def route(self, request: RoutingRequest) -> RoutingDecision:
        model = request.allowed_models[int(self.rng.integers(len(request.allowed_models)))]
        return RoutingDecision(model, {"seed": self.seed})


class FixedRouter(Router):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    def route(self, request: RoutingRequest) -> RoutingDecision:
        if self.model_id not in request.allowed_models:
            raise ValueError("Fixed model is not allowed")
        return RoutingDecision(self.model_id)


class CheapestRouter(Router):
    def __init__(self, expected_costs: dict[str, float]) -> None:
        self.expected_costs = expected_costs

    def route(self, request: RoutingRequest) -> RoutingDecision:
        candidates = [m for m in request.allowed_models if m in self.expected_costs]
        if request.max_expected_cost is not None:
            candidates = [
                m for m in candidates if self.expected_costs[m] <= request.max_expected_cost
            ]
        if not candidates:
            raise ValueError("No model has a known expected cost within the constraint")
        model = min(candidates, key=lambda m: (self.expected_costs[m], m))
        return RoutingDecision(model, {"expected_cost": self.expected_costs[model]})


class TaskAwareRouter(Router):
    def __init__(self, model_by_task: dict[str, str], fallback: str) -> None:
        self.model_by_task, self.fallback = model_by_task, fallback

    def route(self, request: RoutingRequest) -> RoutingDecision:
        task = str(request.features.get("task_type", "other"))
        model = self.model_by_task.get(task, self.fallback)
        if model not in request.allowed_models:
            model = self.fallback
        return RoutingDecision(model, {"task_type": task, "metadata_assisted": True})


class TfidfSuccessRouter(Router):
    """One regularized binary success predictor per candidate model."""

    def __init__(self, *, max_features: int = 30_000, c: float = 1.0, seed: int = 3407):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, max_features=max_features, sublinear_tf=True
        )
        self.c, self.seed = c, seed
        self.models: dict[str, LogisticRegression | float] = {}
        self.expected_costs: dict[str, float] = {}
        self.cost_penalty = 0.0

    def fit(
        self,
        texts: list[str],
        outcomes: dict[str, np.ndarray],
        *,
        expected_costs: dict[str, float] | None = None,
    ) -> TfidfSuccessRouter:
        if len(texts) <= 4:
            self.vectorizer.set_params(min_df=1)
        x = self.vectorizer.fit_transform(texts)
        for model, values in outcomes.items():
            y = np.asarray(values, dtype=float)
            mask = np.isfinite(y)
            labels = (y[mask] >= 1.0).astype(int)
            if not mask.any() or np.unique(labels).size == 1:
                self.models[model] = float(labels[0]) if len(labels) else 0.0
            else:
                clf = LogisticRegression(C=self.c, max_iter=300, random_state=self.seed)
                clf.fit(x[mask], labels)
                self.models[model] = clf
        self.expected_costs = expected_costs or {}
        return self

    def set_cost_penalty(self, value: float) -> None:
        self.cost_penalty = value

    def predict_utilities(self, text: str, allowed: tuple[str, ...]) -> dict[str, float]:
        x: csr_matrix = self.vectorizer.transform([text])
        result = {}
        for model in allowed:
            predictor = self.models[model]
            probability = (
                float(predictor)
                if isinstance(predictor, float)
                else float(predictor.predict_proba(x)[0, 1])
            )
            result[model] = probability - self.cost_penalty * self.expected_costs.get(model, 0.0)
        return result

    def route(self, request: RoutingRequest) -> RoutingDecision:
        allowed = tuple(
            m
            for m in request.allowed_models
            if request.max_expected_cost is None
            or (m in self.expected_costs and self.expected_costs[m] <= request.max_expected_cost)
        )
        if not allowed:
            raise ValueError("No candidate within expected-cost constraint")
        utilities = self.predict_utilities(request.text, allowed)
        selected = max(allowed, key=lambda m: (utilities[m], m))
        return RoutingDecision(
            selected, {"utilities": utilities, "cost_penalty": self.cost_penalty}
        )


def oracle_decision(
    outcomes: dict[str, float], costs: dict[str, float] | None = None
) -> RoutingDecision:
    """Post-hoc upper bound; intentionally not a Router implementation."""
    valid = {m: q for m, q in outcomes.items() if np.isfinite(q)}
    if not valid:
        raise ValueError("Oracle has no observed outcome")
    best = max(valid.values())
    tied = [m for m, value in valid.items() if value == best]
    if costs is not None:
        known = [m for m in tied if m in costs and np.isfinite(costs[m])]
        if known:
            tied = known
            selected = min(tied, key=lambda m: (costs[m], m))
            return RoutingDecision(selected, {"post_hoc": True, "quality": best})
    return RoutingDecision(sorted(tied)[0], {"post_hoc": True, "quality": best})
