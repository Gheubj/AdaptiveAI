from __future__ import annotations

import json
import threading
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from adaptiveai import __version__
from adaptiveai.auto_routing import AutoRoutingPolicy, InsufficientEvidenceError
from adaptiveai.cloud import ProviderError
from adaptiveai.cloud_gateway import CloudGateway
from adaptiveai.config import ProductConfig
from adaptiveai.lifecycle import ModelManager
from adaptiveai.local_backend import BackendError
from adaptiveai.product_registry import ModelRegistry
from adaptiveai.public import ChatMessage, InferenceRequest, ProviderScope, RoutingMode


class MessagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=262_144)


class ChatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[MessagePayload] = Field(min_length=1, max_length=128)
    model: str | None = None
    routing_mode: RoutingMode = RoutingMode.BALANCED
    temperature: float = Field(0.0, ge=0, le=2)
    max_tokens: int = Field(64, ge=1, le=4096)
    stream: bool = False
    timeout: float | None = Field(None, gt=0, le=3600)
    local_only: bool = True
    max_latency_seconds: float | None = Field(None, gt=0)
    available_memory_bytes: int | None = Field(None, gt=0)
    provider_scope: ProviderScope = ProviderScope.LOCAL
    provider: str | None = None
    provider_allowlist: tuple[str, ...] = ()
    max_estimated_cost: float | None = Field(None, ge=0)
    max_total_cost: float | None = Field(None, ge=0)
    cost_currency: str | None = Field(None, pattern=r"^[A-Z]{3}$")
    strict_budget: bool = True
    fallback_models: tuple[str, ...] = ()
    required_capabilities: frozenset[str] = frozenset({"text"})
    minimum_context_tokens: int | None = Field(None, ge=1)

    @field_validator("model")
    @classmethod
    def normalize_auto(cls, value: str | None) -> str | None:
        return None if value in {None, "auto", "adaptiveai"} else value


class ProductService:
    def __init__(
        self,
        manager: ModelManager,
        registry: ModelRegistry | None,
        config: ProductConfig,
        cloud_gateway: CloudGateway | None = None,
        auto_router: AutoRoutingPolicy | None = None,
    ):
        self.manager, self.registry, self.config = manager, registry, config
        self.cloud_gateway = cloud_gateway
        self.auto_router = auto_router

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "lifecycle": self.manager.status(),
            "cloud": self.cloud_gateway.diagnostics() if self.cloud_gateway else [],
            "experimental": True,
        }

    def models(self) -> dict[str, object]:
        data = []
        if self.registry:
            for status in self.registry.inspect():
                data.append(
                    {
                        "id": status.model.model_id,
                        "object": "model",
                        "owned_by": "local",
                        "available": status.available,
                        "family": status.model.family,
                        "quantization": status.model.quantization,
                    }
                )
        if self.cloud_gateway:
            for provider in self.cloud_gateway.diagnostics():
                for model in provider["configured_models"]:
                    data.append(
                        {
                            "id": model,
                            "object": "model",
                            "owned_by": provider["provider"],
                            "available": provider["available"],
                            "status": "configured",
                            "quality": "unknown",
                        }
                    )
        return {"object": "list", "data": data}

    def providers(self) -> dict[str, object]:
        data = self.cloud_gateway.diagnostics() if self.cloud_gateway else []
        return {"object": "list", "data": data}

    @staticmethod
    def _use_cloud(request: InferenceRequest) -> bool:
        if request.local_only or request.provider_scope == ProviderScope.LOCAL:
            return False
        if request.provider_scope == ProviderScope.CLOUD:
            return True
        # Hybrid is explicit: naming a cloud provider selects cloud; otherwise local remains local.
        return request.provider is not None

    def request(self, payload: ChatPayload) -> InferenceRequest:
        return InferenceRequest(
            messages=tuple(ChatMessage(item.role, item.content) for item in payload.messages),
            model=payload.model,
            routing_mode=payload.routing_mode,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            timeout_seconds=payload.timeout or self.config.request_timeout_seconds,
            stream=payload.stream,
            local_only=payload.local_only or self.config.local_only,
            max_latency_seconds=payload.max_latency_seconds or self.config.max_latency_seconds,
            available_memory_bytes=(
                payload.available_memory_bytes or self.config.available_memory_bytes
            ),
            provider_scope=payload.provider_scope,
            provider=payload.provider,
            provider_allowlist=payload.provider_allowlist,
            max_estimated_cost=payload.max_estimated_cost,
            max_total_cost=payload.max_total_cost,
            cost_currency=payload.cost_currency,
            strict_budget=payload.strict_budget,
            fallback_models=payload.fallback_models,
            required_capabilities=payload.required_capabilities,
            minimum_context_tokens=payload.minimum_context_tokens,
        )

    def resolve(self, request: InferenceRequest):
        if request.routing_mode in {RoutingMode.AUTO, RoutingMode.ECONOMY, RoutingMode.MANUAL}:
            if self.auto_router is None:
                raise ValueError("automatic routing is not configured")
            return self.auto_router.select(request)
        return None

    def explain(self, payload: ChatPayload) -> dict[str, object]:
        request = self.request(payload)
        if request.routing_mode not in {RoutingMode.AUTO, RoutingMode.ECONOMY, RoutingMode.MANUAL}:
            raise ValueError("route explanation requires auto, economy, or manual mode")
        if self.auto_router is None:
            raise ValueError("automatic routing is not configured")
        return self.auto_router.explain(request).model_dump(mode="json")

    def complete(self, payload: ChatPayload) -> dict[str, object]:
        request = self.request(payload)
        selection = self.resolve(request)
        if selection:
            request = selection.request
        if self._use_cloud(request):
            if self.cloud_gateway is None:
                raise ValueError("no cloud provider gateway is configured")
            result = self.cloud_gateway.complete(request)
        else:
            result = self.manager.complete(request)
        if selection:
            result = replace(
                result,
                diagnostics=replace(
                    result.diagnostics,
                    mode=selection.decision.mode,
                    reason=selection.decision.selection_reason,
                    explanation=selection.decision.model_dump(mode="json"),
                ),
            )
        return {
            "id": result.request_id,
            "object": "chat.completion",
            "model": result.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": result.text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": (
                    result.prompt_tokens + result.completion_tokens
                    if result.prompt_tokens is not None and result.completion_tokens is not None
                    else None
                ),
            },
            "routing": asdict(result.diagnostics),
        }


def make_handler(service: ProductService, config: ProductConfig):
    semaphore = threading.BoundedSemaphore(config.max_concurrency)

    class Handler(BaseHTTPRequestHandler):
        server_version = f"AdaptiveAI/{__version__}"

        def _json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: int, kind: str, message: str) -> None:
            self._json(status, {"error": {"type": kind, "message": message}})

        def do_GET(self) -> None:
            if self.path == "/health":
                self._json(200, service.health())
            elif self.path == "/v1/models":
                self._json(200, service.models())
            elif self.path == "/v1/providers":
                self._json(200, service.providers())
            else:
                self._error(404, "not_found", "endpoint not found")

        def do_POST(self) -> None:
            if self.path not in {"/v1/chat/completions", "/v1/route/explain"}:
                self._error(404, "not_found", "endpoint not found")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._error(400, "invalid_request", "invalid Content-Length")
                return
            if length <= 0 or length > config.max_request_bytes:
                self._error(413, "request_too_large", "request body exceeds configured limit")
                return
            if not semaphore.acquire(blocking=False):
                self._error(429, "busy", "maximum concurrent requests reached")
                return
            try:
                raw = self.rfile.read(length)
                payload = ChatPayload.model_validate_json(raw)
                if self.path == "/v1/route/explain":
                    self._json(200, service.explain(payload))
                elif payload.stream:
                    self._stream(payload)
                else:
                    self._json(200, service.complete(payload))
            except ValidationError as error:
                self._error(400, "invalid_request", str(error))
            except InsufficientEvidenceError as error:
                self._json(
                    422,
                    {
                        "error": {"type": "INSUFFICIENT_EVIDENCE", "message": str(error)},
                        "routing": error.decision.model_dump(mode="json"),
                    },
                )
            except ValueError as error:
                self._error(400, "routing_error", str(error))
            except BackendError as error:
                status = 504 if "timed out" in str(error) else 503
                self._error(status, "backend_error", str(error))
            except ProviderError as error:
                status = (
                    429 if error.kind == "rate_limit" else 504 if error.kind == "timeout" else 502
                )
                self._error(status, error.kind, str(error))
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception:
                self._error(500, "internal_error", "internal server error")
            finally:
                semaphore.release()

        def _stream(self, payload: ChatPayload) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            request = service.request(payload)
            selection = service.resolve(request)
            if selection:
                request = selection.request
            if service._use_cloud(request):
                if service.cloud_gateway is None:
                    raise ValueError("no cloud provider gateway is configured")
                events = service.cloud_gateway.stream(request)
            else:
                events = service.manager.stream(request)
            try:
                for event in events:
                    if event["type"] == "content":
                        body = {
                            "id": event["request_id"],
                            "object": "chat.completion.chunk",
                            "model": event["model"],
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": event["content"]},
                                    "finish_reason": None,
                                }
                            ],
                        }
                    elif event["type"] == "usage":
                        body = {"id": event["request_id"], "usage": event["usage"]}
                    else:
                        diagnostics = event["diagnostics"]
                        if selection:
                            diagnostics = replace(
                                diagnostics,
                                mode=selection.decision.mode,
                                reason=selection.decision.selection_reason,
                                explanation=selection.decision.model_dump(mode="json"),
                            )
                        body = {
                            "id": event["request_id"],
                            "object": "chat.completion.chunk",
                            "model": event["model"],
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                            "routing": asdict(diagnostics),
                        }
                    self.wfile.write(f"data: {json.dumps(body)}\n\n".encode())
                    self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                events.close()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return Handler


def serve(service: ProductService, config: ProductConfig) -> None:
    server = ThreadingHTTPServer((config.host, config.port), make_handler(service, config))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        service.manager.shutdown()
        if service.cloud_gateway:
            service.cloud_gateway.close()
