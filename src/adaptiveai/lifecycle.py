from __future__ import annotations

import socket
import threading
import time
import uuid
from collections import deque
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

from adaptiveai.local_backend import BackendError, InferenceParameters, LlamaCppServer
from adaptiveai.product_registry import ModelRegistry
from adaptiveai.public import InferenceRequest, InferenceResponse, RoutingDiagnostics, RoutingMode
from adaptiveai.routing_engine import RoutingEngine


class ModelManager:
    """One-resident-model lifecycle manager with bounded, explicit switching behavior."""

    def __init__(
        self,
        registry: ModelRegistry,
        router: RoutingEngine,
        server_binary: Path,
        *,
        keep_alive_seconds: float = 300,
        switch_hysteresis_seconds: float = 0.5,
        port: int | None = None,
    ):
        if not server_binary.is_file():
            raise BackendError(f"llama.cpp server unavailable: {server_binary}")
        self.registry = registry
        self.router = router
        self.server_binary = server_binary
        self.keep_alive_seconds = keep_alive_seconds
        self.switch_hysteresis_seconds = switch_hysteresis_seconds
        self.port = port
        self.current_model: str | None = None
        self.loading = False
        self.healthy = True
        self.last_used_at: float | None = None
        self.recent_requests: deque[tuple[str, float]] = deque(maxlen=32)
        self._server: LlamaCppServer | None = None
        self._lock = threading.RLock()

    @staticmethod
    def _free_local_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            return int(listener.getsockname()[1])

    def status(self) -> dict[str, object]:
        process_alive = bool(
            self._server and self._server.process and self._server.process.poll() is None
        )
        return {
            "current_model": self.current_model,
            "loading": self.loading,
            "healthy": self.healthy and (process_alive or self.current_model is None),
            "recent_requests": len(self.recent_requests),
            "keep_alive_seconds": self.keep_alive_seconds,
        }

    def _apply_stickiness(
        self, request: InferenceRequest, decision: RoutingDiagnostics
    ) -> RoutingDiagnostics:
        if (
            request.model
            or request.routing_mode not in {RoutingMode.BALANCED, RoutingMode.HARDWARE_AWARE}
            or not self.current_model
            or self.current_model == decision.selected_model
            or self.current_model not in decision.eligible_models
        ):
            return decision
        current = self.router.profiles[self.current_model]
        candidate = self.router.profiles[decision.selected_model]
        current_quality, candidate_quality = current.estimated_quality, candidate.estimated_quality
        if current_quality is None or candidate_quality is None:
            return decision
        quality_benefit = candidate_quality - current_quality
        switch_cost = (candidate.loading_seconds or 0) + self.switch_hysteresis_seconds
        required_benefit = self.router.balanced_latency_weight * switch_cost
        if quality_benefit >= required_benefit:
            return decision
        return RoutingDiagnostics(
            selected_model=current.model_id,
            mode=decision.mode,
            reason="kept loaded model because predicted benefit was below switching hysteresis",
            eligible_models=decision.eligible_models,
            predicted_latency_seconds=current.predicted_p95_latency_seconds,
            estimated_quality=current.estimated_quality,
            fallback_reason=(
                f"quality benefit {quality_benefit:.4f} < switching threshold "
                f"{required_benefit:.4f}"
            ),
            experimental=True,
            constraints=decision.constraints,
        )

    def _ensure_loaded(self, model_id: str) -> float:
        if self._server and self.current_model == model_id:
            if self._server.process and self._server.process.poll() is None:
                return 0.0
            self.healthy = False
            self._server.stop()
            self._server = None
            self.current_model = None
        if self._server:
            self._server.stop()
            self._server = None
            self.current_model = None
        model = self.registry.get(model_id)
        self.loading = True
        try:
            server = LlamaCppServer(
                self.server_binary, model, port=self.port or self._free_local_port()
            )
            load_seconds = server.start()
            self._server = server
            self.current_model = model_id
            self.healthy = True
            return load_seconds
        except Exception:
            self.healthy = False
            self.current_model = None
            if self._server:
                self._server.stop()
                self._server = None
            raise
        finally:
            self.loading = False

    @staticmethod
    def _prompt(request: InferenceRequest) -> str:
        return "\n".join(f"{message.role}: {message.content}" for message in request.messages)

    def complete(self, request: InferenceRequest) -> InferenceResponse:
        with self._lock:
            self.unload_if_idle()
            decision = self._apply_stickiness(request, self.router.select(request))
            load_seconds = self._ensure_loaded(decision.selected_model)
            assert self._server is not None
            parameters = InferenceParameters(
                max_tokens=request.max_tokens, temperature=request.temperature
            )
            try:
                result = self._server.infer(
                    self._prompt(request), parameters, timeout=request.timeout_seconds
                )
            except BackendError:
                self.healthy = False
                raise
            now = time.monotonic()
            self.last_used_at = now
            self.recent_requests.append((decision.selected_model, now))
            diagnostics = replace(
                decision,
                measured_latency_seconds=result.elapsed_seconds,
                loading_seconds=load_seconds,
            )
            return InferenceResponse(
                request_id=result.request_id,
                model=result.model_id,
                text=result.text,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.generated_tokens,
                diagnostics=diagnostics,
            )

    def stream(self, request: InferenceRequest) -> Iterator[dict[str, object]]:
        with self._lock:
            self.unload_if_idle()
            decision = self._apply_stickiness(request, self.router.select(request))
            load_seconds = self._ensure_loaded(decision.selected_model)
            assert self._server is not None
            request_id = str(uuid.uuid4())
            parameters = InferenceParameters(
                max_tokens=request.max_tokens, temperature=request.temperature
            )
            started = time.perf_counter()
            try:
                for event in self._server.stream_events(
                    self._prompt(request), parameters, timeout=request.timeout_seconds
                ):
                    yield {"request_id": request_id, "model": decision.selected_model, **event}
            except GeneratorExit:
                # The request is cancelled from the API's perspective. llama.cpp closes the HTTP
                # stream when the generator/context exits; no automatic duplicate retry occurs.
                return
            except BackendError:
                self.healthy = False
                raise
            finally:
                now = time.monotonic()
                self.last_used_at = now
                self.recent_requests.append((decision.selected_model, now))
            yield {
                "type": "done",
                "request_id": request_id,
                "model": decision.selected_model,
                "diagnostics": replace(
                    decision,
                    measured_latency_seconds=time.perf_counter() - started,
                    loading_seconds=load_seconds,
                ),
            }

    def unload_if_idle(self) -> bool:
        with self._lock:
            if (
                not self._server
                or self.last_used_at is None
                or time.monotonic() - self.last_used_at < self.keep_alive_seconds
            ):
                return False
            self._server.stop()
            self._server = None
            self.current_model = None
            return True

    def shutdown(self) -> None:
        with self._lock:
            if self._server:
                self._server.stop()
            self._server = None
            self.current_model = None
