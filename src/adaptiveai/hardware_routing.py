from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class ModelEstimate:
    model_id: str
    provider: Literal["local", "cloud"]
    predicted_quality: float
    predicted_p95_latency: float
    memory_bytes: int
    available: bool = True
    loaded: bool = False
    loading_seconds: float = 0.0
    expected_cost: float = 0.0


@dataclass(frozen=True)
class RoutingConstraints:
    local_only: bool = True
    available_memory_bytes: int | None = None
    max_p95_latency: float | None = None
    max_expected_cost: float | None = None
    quality_threshold: float | None = None
    preference: Literal["quality", "latency"] = "quality"


@dataclass(frozen=True)
class HardwareDecision:
    model_id: str
    policy: str
    provenance: dict[str, object] = field(default_factory=dict)


def eligible_models(
    estimates: tuple[ModelEstimate, ...], constraints: RoutingConstraints
) -> tuple[ModelEstimate, ...]:
    result = []
    for model in estimates:
        if not model.available or (constraints.local_only and model.provider != "local"):
            continue
        if (
            constraints.available_memory_bytes is not None
            and model.memory_bytes > constraints.available_memory_bytes
        ):
            continue
        latency = model.predicted_p95_latency + (0 if model.loaded else model.loading_seconds)
        if constraints.max_p95_latency is not None and latency > constraints.max_p95_latency:
            continue
        if (
            constraints.max_expected_cost is not None
            and model.expected_cost > constraints.max_expected_cost
        ):
            continue
        if (
            constraints.quality_threshold is not None
            and model.predicted_quality < constraints.quality_threshold
        ):
            continue
        result.append(model)
    return tuple(result)


def route_hardware_aware(
    estimates: tuple[ModelEstimate, ...],
    constraints: RoutingConstraints,
    *,
    policy: str = "hardware_aware",
    seed: int = 3407,
) -> HardwareDecision:
    eligible = eligible_models(estimates, constraints)
    if not eligible:
        raise ValueError(
            "No model satisfies availability, privacy, memory, latency, and cost constraints"
        )
    if policy == "fixed_fastest" or constraints.preference == "latency":
        chosen = min(eligible, key=lambda m: (m.predicted_p95_latency, -m.predicted_quality))
    elif policy in {"fixed_strongest", "quality_only", "hardware_aware"}:
        chosen = max(eligible, key=lambda m: (m.predicted_quality, -m.predicted_p95_latency))
    elif policy == "random":
        chosen = eligible[int(np.random.default_rng(seed).integers(len(eligible)))]
    else:
        raise ValueError(f"Unknown routing policy: {policy}")
    return HardwareDecision(
        model_id=chosen.model_id,
        policy=policy,
        provenance={
            "eligible_models": [model.model_id for model in eligible],
            "predicted_quality": chosen.predicted_quality,
            "predicted_p95_latency": chosen.predicted_p95_latency,
            "memory_bytes": chosen.memory_bytes,
            "provider": chosen.provider,
            "loaded": chosen.loaded,
            "constraints": constraints.__dict__,
        },
    )
