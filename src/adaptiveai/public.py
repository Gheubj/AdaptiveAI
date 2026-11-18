from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class RoutingMode(StrEnum):
    FASTEST = "fastest"
    QUALITY = "quality"
    BALANCED = "balanced"
    HARDWARE_AWARE = "hardware-aware"


class ProviderScope(StrEnum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class InferenceRequest:
    messages: tuple[ChatMessage, ...]
    model: str | None = None
    routing_mode: RoutingMode = RoutingMode.BALANCED
    temperature: float = 0.0
    max_tokens: int = 64
    timeout_seconds: float = 120.0
    stream: bool = False
    local_only: bool = True
    max_latency_seconds: float | None = None
    available_memory_bytes: int | None = None
    provider_scope: ProviderScope = ProviderScope.LOCAL
    provider: str | None = None
    provider_allowlist: tuple[str, ...] = ()
    max_estimated_cost: float | None = None
    max_total_cost: float | None = None
    strict_budget: bool = True
    fallback_models: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoutingDiagnostics:
    selected_model: str
    mode: str
    reason: str
    eligible_models: tuple[str, ...]
    predicted_latency_seconds: float | None = None
    estimated_quality: float | None = None
    measured_latency_seconds: float | None = None
    loading_seconds: float | None = None
    fallback_reason: str | None = None
    experimental: bool = False
    constraints: dict[str, object] = field(default_factory=dict)
    provider: str = "local"
    estimated_cost: float | None = None
    actual_cost: float | None = None
    usage_source: str | None = None


@dataclass(frozen=True)
class InferenceResponse:
    request_id: str
    model: str
    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    diagnostics: RoutingDiagnostics


class ModelProvider(Protocol):
    provider_id: str
    is_local: bool

    def list_models(self) -> tuple[str, ...]: ...


class RoutingPolicy(Protocol):
    def select(self, request: InferenceRequest) -> RoutingDiagnostics: ...
