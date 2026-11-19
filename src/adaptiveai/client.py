from __future__ import annotations

import json
from collections.abc import Iterator

import httpx


class AdaptiveAIClient:
    """Small client for AdaptiveAI's documented OpenAI-compatible subset."""

    def __init__(self, base_url: str = "http://127.0.0.1:8088", timeout: float = 120):
        self.base_url, self.timeout = base_url.rstrip("/"), timeout

    def chat(
        self,
        content: str,
        *,
        model: str = "auto",
        routing_mode: str = "balanced",
        max_tokens: int = 64,
        provider_scope: str = "local",
        provider: str | None = None,
        local_only: bool = True,
        max_estimated_cost: float | None = None,
        max_total_cost: float | None = None,
        cost_currency: str | None = None,
        strict_budget: bool = True,
        provider_allowlist: tuple[str, ...] = (),
        fallback_models: tuple[str, ...] = (),
    ) -> dict[str, object]:
        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "routing_mode": routing_mode,
                "max_tokens": max_tokens,
                "provider_scope": provider_scope,
                "provider": provider,
                "local_only": local_only,
                "max_estimated_cost": max_estimated_cost,
                "max_total_cost": max_total_cost,
                "cost_currency": cost_currency,
                "strict_budget": strict_budget,
                "provider_allowlist": provider_allowlist,
                "fallback_models": fallback_models,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def stream(
        self,
        content: str,
        *,
        model: str = "auto",
        routing_mode: str = "balanced",
        provider_scope: str = "local",
        provider: str | None = None,
        local_only: bool = True,
        max_estimated_cost: float | None = None,
        max_total_cost: float | None = None,
        cost_currency: str | None = None,
        strict_budget: bool = True,
        provider_allowlist: tuple[str, ...] = (),
    ) -> Iterator[dict[str, object]]:
        with httpx.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "routing_mode": routing_mode,
                "stream": True,
                "provider_scope": provider_scope,
                "provider": provider,
                "local_only": local_only,
                "max_estimated_cost": max_estimated_cost,
                "max_total_cost": max_total_cost,
                "cost_currency": cost_currency,
                "strict_budget": strict_budget,
                "provider_allowlist": provider_allowlist,
            },
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                yield json.loads(line[6:])

    def route_explain(
        self,
        content: str,
        *,
        routing_mode: str = "auto",
        provider_scope: str = "hybrid",
        local_only: bool = False,
        max_tokens: int = 64,
        max_estimated_cost: float | None = None,
    ) -> dict[str, object]:
        response = httpx.post(
            f"{self.base_url}/v1/route/explain",
            json={
                "messages": [{"role": "user", "content": content}],
                "routing_mode": routing_mode,
                "provider_scope": provider_scope,
                "local_only": local_only,
                "max_tokens": max_tokens,
                "max_estimated_cost": max_estimated_cost,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
