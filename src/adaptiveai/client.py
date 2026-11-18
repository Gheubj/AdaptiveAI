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
    ) -> dict[str, object]:
        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "routing_mode": routing_mode,
                "max_tokens": max_tokens,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def stream(
        self, content: str, *, model: str = "auto", routing_mode: str = "balanced"
    ) -> Iterator[dict[str, object]]:
        with httpx.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "routing_mode": routing_mode,
                "stream": True,
            },
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                yield json.loads(line[6:])
