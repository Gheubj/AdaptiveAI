from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from adaptiveai.public import InferenceRequest, RoutingDiagnostics, RoutingMode


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    provider: str = "local"
    available: bool = True
    estimated_quality: float | None = None
    predicted_p95_latency_seconds: float | None = None
    memory_bytes: int | None = None
    loading_seconds: float | None = None


def load_model_profiles(path: Path, model_ids: tuple[str, ...]) -> tuple[ModelProfile, ...]:
    payload = json.loads(path.read_text()) if path.exists() else {"models": {}}
    rows = payload.get("models", {})
    return tuple(
        ModelProfile(model_id=model_id, **rows.get(model_id, {})) for model_id in model_ids
    )


class RoutingEngine:
    def __init__(
        self, profiles: tuple[ModelProfile, ...], *, balanced_latency_weight: float = 0.15
    ):
        self.profiles = {profile.model_id: profile for profile in profiles}
        self.balanced_latency_weight = balanced_latency_weight

    def eligible(self, request: InferenceRequest) -> tuple[ModelProfile, ...]:
        eligible = []
        for profile in self.profiles.values():
            if not profile.available or (request.local_only and profile.provider != "local"):
                continue
            if (
                request.available_memory_bytes is not None
                and profile.memory_bytes is not None
                and profile.memory_bytes > request.available_memory_bytes
            ):
                continue
            predicted = profile.predicted_p95_latency_seconds
            if (
                request.max_latency_seconds is not None
                and predicted is not None
                and predicted > request.max_latency_seconds
            ):
                continue
            eligible.append(profile)
        return tuple(eligible)

    def select(self, request: InferenceRequest) -> RoutingDiagnostics:
        eligible = self.eligible(request)
        if request.model:
            if request.model not in self.profiles:
                raise ValueError(f"Unknown model: {request.model}")
            matches = [profile for profile in eligible if profile.model_id == request.model]
            if not matches:
                raise ValueError(
                    f"Explicit model is unavailable or violates constraints: {request.model}"
                )
            return self._diagnostics(matches[0], request, "explicit model selection")
        if not eligible:
            raise ValueError(
                "No model satisfies availability, privacy, memory, and latency constraints"
            )

        mode = request.routing_mode
        if mode == RoutingMode.FASTEST:
            known = [p for p in eligible if p.predicted_p95_latency_seconds is not None]
            if not known:
                raise ValueError("Fastest routing requires latency profiles; none are available")
            selected = min(known, key=lambda p: (p.predicted_p95_latency_seconds, p.model_id))
            reason = "lowest profiled p95 latency among eligible models"
        elif mode == RoutingMode.QUALITY:
            known = [p for p in eligible if p.estimated_quality is not None]
            if not known:
                raise ValueError("Quality routing requires validation quality estimates")
            selected = max(
                known,
                key=lambda p: (
                    p.estimated_quality,
                    -(p.predicted_p95_latency_seconds or float("inf")),
                ),
            )
            reason = "highest validation-defined quality estimate among eligible models"
        elif mode == RoutingMode.BALANCED:
            known = [
                p
                for p in eligible
                if p.estimated_quality is not None and p.predicted_p95_latency_seconds is not None
            ]
            if not known:
                raise ValueError("Balanced routing requires quality and latency estimates")
            selected = max(
                known,
                key=lambda p: (
                    p.estimated_quality
                    - self.balanced_latency_weight * p.predicted_p95_latency_seconds
                ),
            )
            reason = (
                "maximum experimental quality - latency_weight * p95_latency objective "
                f"(weight={self.balanced_latency_weight:g})"
            )
        elif mode == RoutingMode.HARDWARE_AWARE:
            known = [p for p in eligible if p.estimated_quality is not None]
            if not known:
                raise ValueError("Hardware-aware routing requires quality estimates")
            selected = max(
                known,
                key=lambda p: (
                    p.estimated_quality,
                    -(p.predicted_p95_latency_seconds or float("inf")),
                ),
            )
            reason = "experimental maximum quality after hardware/privacy constraints"
        else:  # pragma: no cover - enum validation normally prevents this
            raise ValueError(f"Unsupported routing mode: {mode}")
        return self._diagnostics(selected, request, reason)

    def _diagnostics(
        self, profile: ModelProfile, request: InferenceRequest, reason: str
    ) -> RoutingDiagnostics:
        return RoutingDiagnostics(
            selected_model=profile.model_id,
            mode=request.routing_mode.value,
            reason=reason,
            eligible_models=tuple(p.model_id for p in self.eligible(request)),
            predicted_latency_seconds=profile.predicted_p95_latency_seconds,
            estimated_quality=profile.estimated_quality,
            experimental=request.routing_mode in {RoutingMode.BALANCED, RoutingMode.HARDWARE_AWARE},
            constraints={
                "local_only": request.local_only,
                "max_latency_seconds": request.max_latency_seconds,
                "available_memory_bytes": request.available_memory_bytes,
            },
        )
