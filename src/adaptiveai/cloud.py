from __future__ import annotations

import ipaddress
import json
import os
import socket
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from adaptiveai.public import ChatMessage


class ProviderError(RuntimeError):
    """Safe provider error whose message never contains a request body or credential."""

    kind = "provider_error"
    retryable = False


class AuthenticationError(ProviderError):
    kind = "authentication"


class InsufficientCreditsError(ProviderError):
    kind = "insufficient_credits"


class RateLimitError(ProviderError):
    kind = "rate_limit"
    retryable = True


class ProviderUnavailableError(ProviderError):
    kind = "unavailable"
    retryable = True


class ProviderTimeoutError(ProviderError):
    kind = "timeout"
    retryable = True


class MalformedResponseError(ProviderError):
    kind = "malformed_response"


class UnsupportedModelError(ProviderError):
    kind = "unsupported_model"


class InvalidProviderRequestError(ProviderError):
    kind = "invalid_request"


class InterruptedStreamError(ProviderError):
    kind = "interrupted_stream"


class BudgetError(ProviderError):
    kind = "budget"


class CapabilityState(StrEnum):
    ADVERTISED = "advertised"
    CONFIGURED = "configured"
    TESTED = "tested"
    UNKNOWN = "unknown"


class ModelPricing(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model: str
    input_per_million: float = Field(ge=0)
    output_per_million: float = Field(ge=0)
    currency: str = "USD"
    source: str
    retrieved_at: str


class CloudProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider_id: str = Field(pattern=r"^[a-zA-Z0-9._-]+$")
    deployment_id: str | None = None
    base_url: str
    api_key_env: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    permitted_models: tuple[str, ...]
    aliases: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: float = Field(60, gt=0, le=3600)
    connect_timeout_seconds: float = Field(10, gt=0, le=120)
    max_response_bytes: int = Field(2_097_152, ge=1024, le=67_108_864)
    max_requests_per_minute: int | None = Field(None, ge=1)
    hosted_mode: bool = True
    strict_ssrf_protection: bool = False
    allow_localhost: bool = False
    allowed_hosts: tuple[str, ...] = ()
    request_parameters: dict[str, Any] = Field(default_factory=dict)
    pricing: tuple[ModelPricing, ...] = ()
    capabilities: dict[str, CapabilityState] = Field(default_factory=dict)

    @field_validator("permitted_models")
    @classmethod
    def nonempty_unique_models(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or len(value) != len(set(value)):
            raise ValueError("permitted_models must be non-empty and unique")
        return value

    @model_validator(mode="after")
    def validate_aliases_and_parameters(self) -> CloudProviderConfig:
        if any(target not in self.permitted_models for target in self.aliases.values()):
            raise ValueError("every alias target must be a permitted model")
        forbidden = {"model", "messages", "stream", "authorization"}
        if forbidden.intersection(key.lower() for key in self.request_parameters):
            raise ValueError("request_parameters cannot override protected fields")
        supported = {"chat_completions", "streaming", "model_discovery", "usage"}
        mandatory_unknown = [
            key[1:]
            for key, value in self.capabilities.items()
            if key.startswith("!")
            and (key[1:] not in supported or value == CapabilityState.UNKNOWN)
        ]
        if mandatory_unknown:
            raise ValueError(f"unknown mandatory capabilities: {sorted(mandatory_unknown)}")
        return self


def validate_endpoint(
    config: CloudProviderConfig,
    resolver: Callable[..., list[tuple[Any, ...]]] = socket.getaddrinfo,
) -> None:
    parsed = urlparse(config.base_url)
    if config.strict_ssrf_protection:
        raise ValueError(
            "strict SSRF protection requires a connection-pinned transport or egress firewall"
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("provider base_url cannot contain credentials, query, or fragment")
    if not parsed.hostname or parsed.scheme not in {"http", "https"}:
        raise ValueError("provider base_url must be an absolute HTTP(S) URL")
    host = parsed.hostname.lower()
    loopback_name = host in {"localhost", "localhost.localdomain"}
    if config.hosted_mode:
        if parsed.scheme != "https":
            raise ValueError("hosted providers require HTTPS")
        if not config.allowed_hosts or host not in {item.lower() for item in config.allowed_hosts}:
            raise ValueError("hosted provider hostname must be explicitly allowlisted")
    elif parsed.scheme == "http" and not (config.allow_localhost and loopback_name):
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if not (config.allow_localhost and literal and literal.is_loopback):
            raise ValueError("plain HTTP is allowed only for explicit localhost developer mode")
    if loopback_name and not config.allow_localhost:
        raise ValueError("localhost requires allow_localhost=true")
    try:
        addresses = {
            row[4][0] for row in resolver(host, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except OSError as error:
        raise ValueError("provider hostname could not be resolved safely") from error
    if not addresses:
        raise ValueError("provider hostname resolved to no addresses")
    for raw in addresses:
        address = ipaddress.ip_address(raw)
        unsafe = (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        )
        if unsafe and not (
            config.allow_localhost and address.is_loopback and not config.hosted_mode
        ):
            raise ValueError("provider hostname resolves to a non-public address")


@dataclass(frozen=True)
class ProviderUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    source: str = "unreported"


@dataclass(frozen=True)
class CloudResponse:
    request_id: str
    provider: str
    model: str
    text: str
    usage: ProviderUsage
    latency_seconds: float


@dataclass(frozen=True)
class CostEstimate:
    model: str
    currency: str
    input_tokens: int
    max_output_tokens: int
    amount: float
    pricing_source: str
    pricing_retrieved_at: str


@dataclass(frozen=True)
class UsageRecord:
    request_id: str
    requested_model: str
    selected_model: str
    provider: str
    status: str
    latency_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None
    usage_source: str
    estimated_cost: float | None
    actual_cost: float | None


@dataclass
class BudgetLedger:
    max_total: float | None = None
    committed: float = 0.0
    reserved: float = 0.0
    records: list[UsageRecord] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def authorize(self, estimate: CostEstimate, per_request: float | None) -> None:
        with self._lock:
            if per_request is not None and estimate.amount > per_request:
                raise BudgetError("estimated request cost exceeds the configured request budget")
            if (
                self.max_total is not None
                and self.committed + self.reserved + estimate.amount > self.max_total
            ):
                raise BudgetError("estimated request cost exceeds the configured total budget")
            self.reserved += estimate.amount

    def release(self, amount: float | None) -> None:
        if amount is None:
            return
        with self._lock:
            self.reserved = max(0.0, self.reserved - amount)

    def record(self, record: UsageRecord) -> None:
        with self._lock:
            if record.estimated_cost is not None:
                self.reserved = max(0.0, self.reserved - record.estimated_cost)
            self.records.append(record)
            if record.status == "succeeded":
                if record.actual_cost is not None:
                    self.committed += record.actual_cost
                elif record.estimated_cost is not None:
                    self.committed += record.estimated_cost


class CloudProvider(Protocol):
    provider_id: str

    def configured_models(self) -> tuple[str, ...]: ...
    def discover_models(self) -> tuple[str, ...]: ...
    def available(self) -> bool: ...
    def complete(
        self, messages: tuple[ChatMessage, ...], model: str, **kwargs: Any
    ) -> CloudResponse: ...
    def stream(
        self, messages: tuple[ChatMessage, ...], model: str, **kwargs: Any
    ) -> Iterator[dict[str, Any]]: ...


class OpenAICompatibleProvider:
    """Bounded OpenAI chat-completions subset; it never retries paid requests."""

    def __init__(
        self,
        config: CloudProviderConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        resolver: Callable[..., list[tuple[Any, ...]]] = socket.getaddrinfo,
    ):
        validate_endpoint(config, resolver)
        self.config = config
        self.provider_id = config.provider_id
        self.deployment_id = config.deployment_id or config.base_url
        self._request_times: deque[float] = deque()
        timeout = httpx.Timeout(config.timeout_seconds, connect=config.connect_timeout_seconds)
        self._client = httpx.Client(
            base_url=config.base_url.rstrip("/"),
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._client.close()

    def _key(self) -> str:
        key = os.getenv(self.config.api_key_env)
        if not key:
            raise AuthenticationError(
                f"credential environment variable {self.config.api_key_env} is not set"
            )
        return key

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key()}", "Accept": "application/json"}

    def configured_models(self) -> tuple[str, ...]:
        return self.config.permitted_models

    def available(self) -> bool:
        return bool(os.getenv(self.config.api_key_env))

    def resolve_model(self, model: str) -> str:
        resolved = self.config.aliases.get(model, model)
        if resolved not in self.config.permitted_models:
            raise UnsupportedModelError("requested model is not in the provider allowlist")
        return resolved

    def discover_models(self) -> tuple[str, ...]:
        self._check_rate_limit()
        try:
            response = self._client.get("/v1/models", headers=self._headers())
            self._raise_status(response)
            self._bounded(response)
            data = response.json().get("data", [])
            advertised = {row["id"] for row in data if isinstance(row, dict) and "id" in row}
        except (ValueError, json.JSONDecodeError, KeyError) as error:
            raise MalformedResponseError("provider returned malformed model metadata") from error
        return tuple(model for model in self.config.permitted_models if model in advertised)

    def estimate(
        self, model: str, input_tokens: int, max_output_tokens: int
    ) -> CostEstimate | None:
        resolved = self.resolve_model(model)
        price = next((item for item in self.config.pricing if item.model == resolved), None)
        if price is None:
            return None
        amount = (
            input_tokens * price.input_per_million + max_output_tokens * price.output_per_million
        ) / 1_000_000
        return CostEstimate(
            resolved,
            price.currency,
            input_tokens,
            max_output_tokens,
            amount,
            price.source,
            price.retrieved_at,
        )

    @staticmethod
    def _message_rows(messages: tuple[ChatMessage, ...]) -> list[dict[str, str]]:
        return [{"role": item.role, "content": item.content} for item in messages]

    def _payload(
        self,
        messages: tuple[ChatMessage, ...],
        model: str,
        *,
        max_tokens: int,
        temperature: float,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            **self.config.request_parameters,
            "model": self.resolve_model(model),
            "messages": self._message_rows(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

    def complete(
        self,
        messages: tuple[ChatMessage, ...],
        model: str,
        *,
        max_tokens: int = 64,
        temperature: float = 0,
    ) -> CloudResponse:
        started = time.perf_counter()
        self._check_rate_limit()
        try:
            response = self._client.post(
                "/v1/chat/completions",
                headers=self._headers(),
                json=self._payload(
                    messages,
                    model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False,
                ),
            )
            self._raise_status(response)
            self._bounded(response)
            row = response.json()
            text = row["choices"][0]["message"]["content"]
            selected = row.get("model") or self.resolve_model(model)
            raw_usage = row.get("usage") or {}
            usage = ProviderUsage(
                raw_usage.get("prompt_tokens"),
                raw_usage.get("completion_tokens"),
                "provider" if raw_usage else "unreported",
            )
            return CloudResponse(
                str(row.get("id") or uuid.uuid4()),
                self.provider_id,
                selected,
                str(text),
                usage,
                time.perf_counter() - started,
            )
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError("provider request timed out") from error
        except httpx.HTTPError as error:
            raise ProviderUnavailableError("provider transport failed") from error
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise MalformedResponseError("provider returned a malformed completion") from error

    def stream(
        self,
        messages: tuple[ChatMessage, ...],
        model: str,
        *,
        max_tokens: int = 64,
        temperature: float = 0,
    ) -> Iterator[dict[str, Any]]:
        request_id = str(uuid.uuid4())
        self._check_rate_limit()
        try:
            with self._client.stream(
                "POST",
                "/v1/chat/completions",
                headers=self._headers(),
                json=self._payload(
                    messages,
                    model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ),
            ) as response:
                self._raise_status(response)
                consumed = 0
                saw_done = False
                for line in response.iter_lines():
                    consumed += len(line.encode())
                    if consumed > self.config.max_response_bytes:
                        raise MalformedResponseError("provider stream exceeded response limit")
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        saw_done = True
                        break
                    try:
                        row = json.loads(data)
                        request_id = str(row.get("id") or request_id)
                        delta = row["choices"][0].get("delta", {}).get("content")
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
                        raise MalformedResponseError(
                            "provider returned malformed stream data"
                        ) from error
                    if delta:
                        yield {"type": "content", "request_id": request_id, "content": str(delta)}
                    if row.get("usage"):
                        yield {"type": "usage", "request_id": request_id, "usage": row["usage"]}
                if not saw_done:
                    raise InterruptedStreamError("provider stream ended before completion")
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError("provider stream timed out") from error
        except httpx.HTTPError as error:
            raise ProviderUnavailableError("provider stream transport failed") from error

    def _bounded(self, response: httpx.Response) -> None:
        if len(response.content) > self.config.max_response_bytes:
            raise MalformedResponseError("provider response exceeded response limit")

    def _check_rate_limit(self) -> None:
        limit = self.config.max_requests_per_minute
        if limit is None:
            return
        now = time.monotonic()
        while self._request_times and now - self._request_times[0] >= 60:
            self._request_times.popleft()
        if len(self._request_times) >= limit:
            raise RateLimitError("configured client-side provider rate limit reached")
        self._request_times.append(now)

    @staticmethod
    def _raise_status(response: httpx.Response) -> None:
        code = response.status_code
        if code < 400:
            return
        if code in {401, 403}:
            raise AuthenticationError("provider rejected authentication")
        if code == 402:
            raise InsufficientCreditsError("provider reported insufficient credits")
        if code == 404:
            raise UnsupportedModelError("provider model or endpoint was not found")
        if code == 429:
            raise RateLimitError("provider rate limit reached")
        if code in {408, 504}:
            raise ProviderTimeoutError("provider request timed out")
        if 400 <= code < 500:
            raise InvalidProviderRequestError("provider rejected the request")
        raise ProviderUnavailableError("provider is unavailable")


class DeterministicOpenAITransport(httpx.BaseTransport):
    """Offline OpenAI-compatible test server; no socket or paid call is possible."""

    def __init__(self, models: tuple[str, ...] = ("mock-model",)):
        self.models = models
        self.requests = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests += 1
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": item} for item in self.models]})
        payload = json.loads(request.content)
        content = payload["messages"][-1]["content"]
        if content == "AUTH_ERROR":
            return httpx.Response(401, json={"error": "redacted"})
        if content == "RATE_LIMIT":
            return httpx.Response(429, json={"error": "redacted"})
        if content == "CRASH":
            return httpx.Response(503, json={"error": "redacted"})
        if content == "MALFORMED":
            return httpx.Response(200, content=b"not-json")
        if payload.get("stream"):
            body = (
                'data: {"id":"mock-id","choices":[{"delta":{"content":"mock "}}]}\n\n'
                'data: {"id":"mock-id","choices":[{"delta":{"content":"response"}}],'
                '"usage":{"prompt_tokens":2,"completion_tokens":2}}\n\n'
                "data: [DONE]\n\n"
            )
            return httpx.Response(
                200, content=body.encode(), headers={"content-type": "text/event-stream"}
            )
        return httpx.Response(
            200,
            json={
                "id": "mock-id",
                "model": payload["model"],
                "choices": [{"message": {"role": "assistant", "content": "mock response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 2},
            },
        )
