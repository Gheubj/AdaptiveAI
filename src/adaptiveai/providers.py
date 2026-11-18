from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model_id: str
    text: str
    expected_cost: float


class InferenceProvider(ABC):
    name: str
    is_local: bool

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def infer(self, model_id: str, prompt: str) -> ProviderResponse: ...


class MockCloudProvider(InferenceProvider):
    """Offline test double. It never performs network I/O."""

    name = "mock-cloud"
    is_local = False

    def __init__(self, responses: dict[str, str] | None = None, *, enabled: bool = False):
        self.responses = responses or {}
        self.enabled = enabled

    def available(self) -> bool:
        return self.enabled

    def infer(self, model_id: str, prompt: str) -> ProviderResponse:
        if not self.enabled:
            raise RuntimeError("Mock cloud provider is disabled")
        return ProviderResponse(self.name, model_id, self.responses.get(prompt, "mock"), 0.0)
