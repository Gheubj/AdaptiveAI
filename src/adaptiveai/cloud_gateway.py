from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import replace

from adaptiveai.cloud import (
    BudgetError,
    BudgetLedger,
    CloudProvider,
    OpenAICompatibleProvider,
    ProviderError,
    UsageRecord,
)
from adaptiveai.public import (
    InferenceRequest,
    InferenceResponse,
    ProviderScope,
    RoutingDiagnostics,
    RoutingMode,
)


class CloudGateway:
    """Explicit cloud execution boundary. Selection is deterministic, not learned."""

    def __init__(
        self,
        providers: tuple[CloudProvider, ...],
        *,
        ledger: BudgetLedger | None = None,
    ):
        self.providers = {item.provider_id: item for item in providers}
        if len(self.providers) != len(providers):
            raise ValueError("provider ids must be unique")
        self.ledger = ledger or BudgetLedger()

    def diagnostics(self) -> list[dict[str, object]]:
        return [
            {
                "provider": item.provider_id,
                "deployment": getattr(item, "deployment_id", "unspecified"),
                "available": item.available(),
                "configured_models": item.configured_models(),
                "model_status": "configured",
                "quality": "unknown",
            }
            for item in self.providers.values()
        ]

    def _select(self, request: InferenceRequest) -> tuple[CloudProvider, str]:
        if request.local_only or request.provider_scope == ProviderScope.LOCAL:
            raise ValueError("cloud execution is forbidden by local-only provider scope")
        if not request.model:
            raise ValueError("cloud execution requires explicit model selection")
        candidates = self.providers
        if request.provider_allowlist:
            candidates = {
                key: value for key, value in candidates.items() if key in request.provider_allowlist
            }
        if request.provider:
            candidates = {
                key: value for key, value in candidates.items() if key == request.provider
            }
        if len(candidates) != 1:
            raise ValueError("cloud execution requires exactly one explicit eligible provider")
        provider = next(iter(candidates.values()))
        if not provider.available():
            raise ValueError("selected cloud provider has no available BYOK credential")
        if request.routing_mode == RoutingMode.QUALITY and request.model is None:
            raise ValueError("quality routing cannot rank cloud models without quality evidence")
        if request.model not in provider.configured_models():
            config = getattr(provider, "config", None)
            if not config or request.model not in config.aliases:
                raise ValueError("model is not permitted for the selected provider")
        return provider, request.model

    @staticmethod
    def _input_estimate(request: InferenceRequest) -> int:
        # Transparent conservative approximation, never presented as provider-reported usage.
        characters = sum(len(item.role) + len(item.content) + 4 for item in request.messages)
        return max(1, (characters + 2) // 3)

    def _authorize(self, provider: CloudProvider, model: str, request: InferenceRequest):
        if not isinstance(provider, OpenAICompatibleProvider):
            if request.strict_budget:
                raise BudgetError("strict budget mode requires known provider pricing")
            return None
        estimate = provider.estimate(model, self._input_estimate(request), request.max_tokens)
        if estimate is None:
            if request.strict_budget:
                raise BudgetError("strict budget mode rejects missing pricing")
            return None
        if estimate.currency != "USD":
            raise BudgetError("budget comparison currently requires USD pricing")
        if request.max_total_cost is not None:
            self.ledger.max_total = request.max_total_cost
        self.ledger.authorize(estimate, request.max_estimated_cost)
        return estimate

    def complete(self, request: InferenceRequest) -> InferenceResponse:
        provider, model = self._select(request)
        estimate = self._authorize(provider, model, request)
        started = time.perf_counter()
        try:
            try:
                result = provider.complete(
                    request.messages,
                    model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
            except ProviderError as first_error:
                # Only an explicit fallback is considered, and only for a rejection that occurs
                # before generation. Rate limits, timeouts, and ambiguous failures are never
                # retried because a duplicate paid request could result.
                from adaptiveai.cloud import UnsupportedModelError

                if (
                    not isinstance(first_error, UnsupportedModelError)
                    or not request.fallback_models
                ):
                    raise
                model = request.fallback_models[0]
                fallback_request = replace(request, model=model, fallback_models=())
                provider, model = self._select(fallback_request)
                estimate = self._authorize(provider, model, fallback_request)
                result = provider.complete(
                    request.messages,
                    model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
            price = None
            if (
                estimate
                and result.usage.prompt_tokens is not None
                and result.usage.completion_tokens is not None
            ):
                configured = provider.estimate(
                    model, result.usage.prompt_tokens, result.usage.completion_tokens
                )
                price = configured.amount if configured else None
            record = UsageRecord(
                result.request_id,
                request.model or model,
                result.model,
                result.provider,
                "succeeded",
                result.latency_seconds,
                result.usage.prompt_tokens,
                result.usage.completion_tokens,
                result.usage.source,
                estimate.amount if estimate else None,
                price,
            )
            self.ledger.record(record)
            diagnostics = RoutingDiagnostics(
                result.model,
                request.routing_mode.value,
                "explicit cloud provider and model selection",
                (result.model,),
                measured_latency_seconds=result.latency_seconds,
                experimental=True,
                constraints={"provider_scope": request.provider_scope.value, "local_only": False},
                provider=result.provider,
                estimated_cost=estimate.amount if estimate else None,
                actual_cost=price,
                usage_source=result.usage.source,
            )
            return InferenceResponse(
                result.request_id,
                result.model,
                result.text,
                result.usage.prompt_tokens,
                result.usage.completion_tokens,
                diagnostics,
            )
        except ProviderError:
            elapsed = time.perf_counter() - started
            self.ledger.record(
                UsageRecord(
                    "unavailable",
                    request.model or model,
                    model,
                    provider.provider_id,
                    "failed",
                    elapsed,
                    None,
                    None,
                    "unreported",
                    estimate.amount if estimate else None,
                    None,
                )
            )
            raise

    def stream(self, request: InferenceRequest) -> Iterator[dict[str, object]]:
        provider, model = self._select(request)
        estimate = self._authorize(provider, model, request)
        started = time.perf_counter()
        request_id = "pending"
        usage: dict[str, object] = {}
        try:
            for event in provider.stream(
                request.messages,
                model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ):
                request_id = str(event.get("request_id", request_id))
                if event["type"] == "usage":
                    usage = dict(event["usage"])
                yield {**event, "model": model}
        except GeneratorExit:
            return
        diagnostics = RoutingDiagnostics(
            model,
            request.routing_mode.value,
            "explicit cloud provider and model selection",
            (model,),
            measured_latency_seconds=time.perf_counter() - started,
            experimental=True,
            constraints={"provider_scope": request.provider_scope.value, "local_only": False},
            provider=provider.provider_id,
            estimated_cost=estimate.amount if estimate else None,
            usage_source="provider" if usage else "unreported",
        )
        actual_cost = None
        if (
            estimate
            and usage.get("prompt_tokens") is not None
            and usage.get("completion_tokens") is not None
            and isinstance(provider, OpenAICompatibleProvider)
        ):
            cost = provider.estimate(
                model, int(usage["prompt_tokens"]), int(usage["completion_tokens"])
            )
            actual_cost = cost.amount if cost else None
        self.ledger.record(
            UsageRecord(
                request_id,
                request.model or model,
                model,
                provider.provider_id,
                "succeeded",
                time.perf_counter() - started,
                int(usage["prompt_tokens"]) if usage.get("prompt_tokens") is not None else None,
                int(usage["completion_tokens"])
                if usage.get("completion_tokens") is not None
                else None,
                "provider" if usage else "unreported",
                estimate.amount if estimate else None,
                actual_cost,
            )
        )
        yield {
            "type": "done",
            "request_id": request_id,
            "model": model,
            "diagnostics": diagnostics,
        }

    def close(self) -> None:
        for provider in self.providers.values():
            close = getattr(provider, "close", None)
            if close:
                close()
