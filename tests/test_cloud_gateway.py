import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from pydantic import ValidationError

from adaptiveai.api import ProductService, make_handler
from adaptiveai.client import AdaptiveAIClient
from adaptiveai.cloud import (
    AuthenticationError,
    BudgetError,
    BudgetLedger,
    CloudProviderConfig,
    CostEstimate,
    DeterministicOpenAITransport,
    InsufficientCreditsError,
    InvalidProviderRequestError,
    MalformedResponseError,
    ModelPricing,
    OpenAICompatibleProvider,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
    external_smoke_plan,
    validate_endpoint,
)
from adaptiveai.cloud_gateway import CloudGateway
from adaptiveai.config import ProductConfig
from adaptiveai.product_registry import ModelRegistry
from adaptiveai.public import ChatMessage, InferenceRequest, ProviderScope


def public_resolver(*_args, **_kwargs):
    return [(2, 1, 6, "", ("8.8.8.8", 443))]


def loopback_resolver(*_args, **_kwargs):
    return [(2, 1, 6, "", ("127.0.0.1", 80))]


def provider_config(**updates):
    base = {
        "provider_id": "mock",
        "base_url": "https://api.example.test",
        "api_key_env": "ADAPTIVEAI_TEST_KEY",
        "permitted_models": ("mock-model",),
        "allowed_hosts": ("api.example.test",),
        "pricing": (
            ModelPricing(
                model="mock-model",
                input_per_million=1.0,
                output_per_million=2.0,
                source="test fixture",
                retrieved_at="2026-11-19",
            ),
        ),
    }
    base.update(updates)
    return CloudProviderConfig(**base)


def make_provider(monkeypatch, **updates):
    monkeypatch.setenv("ADAPTIVEAI_TEST_KEY", "super-secret-value")
    transport = DeterministicOpenAITransport()
    provider = OpenAICompatibleProvider(
        provider_config(**updates), transport=transport, resolver=public_resolver
    )
    return provider, transport


def cloud_request(content="hello", **updates):
    base = {
        "messages": (ChatMessage("user", content),),
        "model": "mock-model",
        "local_only": False,
        "provider_scope": ProviderScope.CLOUD,
        "provider": "mock",
        "max_tokens": 10,
        "max_estimated_cost": 1.0,
    }
    base.update(updates)
    return InferenceRequest(**base)


def test_configuration_endpoint_and_capability_guards():
    with pytest.raises(ValidationError, match="alias target"):
        provider_config(aliases={"bad": "not-allowed"})
    with pytest.raises(ValidationError, match="mandatory"):
        provider_config(capabilities={"!magic": "unknown"})
    with pytest.raises(ValueError, match="HTTPS"):
        validate_endpoint(
            provider_config(base_url="http://api.example.test"), resolver=public_resolver
        )
    with pytest.raises(ValueError, match="allowlisted"):
        validate_endpoint(provider_config(allowed_hosts=()), resolver=public_resolver)
    with pytest.raises(ValueError, match="connection-pinned"):
        validate_endpoint(provider_config(strict_ssrf_protection=True), resolver=public_resolver)
    local = provider_config(
        base_url="http://localhost:8080",
        hosted_mode=False,
        allow_localhost=True,
        allowed_hosts=(),
    )
    validate_endpoint(local, resolver=loopback_resolver)


def test_external_smoke_plan_is_non_executing_and_fail_closed():
    pinned = provider_config(
        provider_id="openrouter",
        deployment_id="free-pinned",
        permitted_models=("vendor/exact:free",),
        pricing=(
            ModelPricing(
                model="vendor/exact:free",
                input_per_million=0,
                output_per_million=0,
                source="official snapshot",
                retrieved_at="2026-11-19",
            ),
        ),
        request_parameters={
            "provider": {
                "only": ["Pinned Upstream"],
                "allow_fallbacks": False,
                "data_collection": "deny",
            }
        },
    )
    plan = external_smoke_plan(pinned, "vendor/exact:free", input_tokens=16, max_output_tokens=8)
    assert plan["status"] == "READY_FOR_OWNER_AUTHORIZATION"
    assert plan["authorization"] == "NOT_AUTHORIZED"
    assert plan["executes_inference"] is False
    assert plan["worst_case_estimated_usd"] == 0
    assert plan["checks"]["data_collection_denied"] is True

    generic = pinned.model_copy(update={"permitted_models": ("openrouter/free",), "pricing": ()})
    blocked = external_smoke_plan(generic, "openrouter/free", input_tokens=16, max_output_tokens=8)
    assert blocked["status"] == "BLOCKED"
    assert blocked["checks"]["exact_non_router_model"] is False


def test_provider_discovery_completion_stream_and_usage(monkeypatch):
    provider, transport = make_provider(monkeypatch)
    assert provider.available()
    assert provider.discover_models() == ("mock-model",)
    result = provider.complete(cloud_request().messages, "mock-model", max_tokens=10)
    assert result.text == "mock response"
    assert result.usage.prompt_tokens == 2
    events = list(provider.stream(cloud_request().messages, "mock-model", max_tokens=10))
    assert "".join(item.get("content", "") for item in events) == "mock response"
    assert any(item["type"] == "usage" for item in events)
    assert transport.requests == 3
    provider.close()


def test_documented_versioned_base_url_is_not_duplicated(monkeypatch):
    monkeypatch.setenv("ADAPTIVEAI_TEST_KEY", "secret")
    paths = []

    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"data": [{"id": "mock-model"}]})

    provider = OpenAICompatibleProvider(
        provider_config(base_url="https://api.example.test/openai/v1"),
        transport=httpx.MockTransport(handler),
        resolver=public_resolver,
    )
    assert provider.discover_models() == ("mock-model",)
    assert paths == ["/openai/v1/models"]
    provider.close()


def test_proxyapi_offline_contract_currency_budget_errors_and_no_retry(monkeypatch):
    monkeypatch.setenv("PROXYAPI_API_KEY", "proxy-secret-fixture")
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "openai/gpt-4.1-mini"}]})
        payload = json.loads(request.content)
        marker = payload["messages"][-1]["content"]
        statuses = {
            "AUTH": 401,
            "BALANCE": 402,
            "RESTRICTED": 403,
            "RATE": 429,
            "UPSTREAM": 502,
            "TIMEOUT": 504,
        }
        if marker in statuses:
            return httpx.Response(statuses[marker], json={"error": "redacted fixture"})
        usage = {} if marker == "NO_USAGE" else {"prompt_tokens": 7, "completion_tokens": 1}
        return httpx.Response(
            200,
            json={
                "id": "proxy-fixture-id",
                "model": "openai/gpt-4.1-mini",
                "choices": [{"message": {"content": "ok"}}],
                "usage": usage,
            },
        )

    config = CloudProviderConfig(
        provider_id="proxyapi",
        deployment_id="proxyapi-unified-v1",
        base_url="https://api.proxyapi.ru/v1",
        api_key_env="PROXYAPI_API_KEY",
        permitted_models=("openai/gpt-4.1-mini",),
        allowed_hosts=("api.proxyapi.ru",),
        timeout_seconds=30,
        connect_timeout_seconds=5,
        max_response_bytes=2048,
        max_requests_per_minute=30,
        pricing=(
            ModelPricing(
                model="openai/gpt-4.1-mini",
                input_per_million="104",
                output_per_million="413",
                currency="RUB",
                source="official ProxyAPI catalog fixture",
                retrieved_at="2026-11-19",
            ),
        ),
    )
    provider = OpenAICompatibleProvider(
        config, transport=httpx.MockTransport(handler), resolver=public_resolver
    )
    assert provider.discover_models() == ("openai/gpt-4.1-mini",)
    assert calls[-1].url.path == "/v1/models"
    assert calls[-1].headers["Authorization"] == "Bearer proxy-secret-fixture"
    estimate = provider.estimate("openai/gpt-4.1-mini", 16, 16)
    assert str(estimate.amount) == "0.008272"
    assert estimate.currency == "RUB"

    gateway = CloudGateway((provider,))

    def request(text="hello", **updates):
        values = {
            "messages": (ChatMessage("user", text),),
            "model": "openai/gpt-4.1-mini",
            "local_only": False,
            "provider_scope": ProviderScope.CLOUD,
            "provider": "proxyapi",
            "max_tokens": 16,
            "max_estimated_cost": 5,
            "cost_currency": "RUB",
        }
        values.update(updates)
        return InferenceRequest(**values)

    with pytest.raises(BudgetError, match="currency"):
        gateway.complete(request(cost_currency="USD"))
    with pytest.raises(BudgetError, match="request budget"):
        gateway.complete(request(max_estimated_cost=0))
    with pytest.raises(ValueError, match="local-only"):
        gateway.complete(request(local_only=True))

    result = gateway.complete(request())
    assert result.text == "ok"
    assert result.diagnostics.cost_currency == "RUB"
    assert result.diagnostics.actual_cost == pytest.approx(0.001141)
    assert gateway.ledger.currency == "RUB"
    assert gateway.ledger.reserved == 0

    no_usage = gateway.complete(request("NO_USAGE"))
    assert no_usage.diagnostics.usage_source == "unreported"

    errors = (
        ("AUTH", AuthenticationError),
        ("BALANCE", InsufficientCreditsError),
        ("RESTRICTED", InvalidProviderRequestError),
        ("RATE", RateLimitError),
        ("UPSTREAM", ProviderUnavailableError),
        ("TIMEOUT", ProviderTimeoutError),
    )
    for marker, error_type in errors:
        before = len(calls)
        with pytest.raises(error_type) as error:
            gateway.complete(request(marker))
        assert len(calls) == before + 1
        assert "proxy-secret-fixture" not in str(error.value)
        assert gateway.ledger.reserved == 0

    assert all(json.loads(call.content).get("stream") is False for call in calls[1:])
    assert all(json.loads(call.content)["model"] == "openai/gpt-4.1-mini" for call in calls[1:])
    gateway.close()


def test_typed_errors_are_redacted(monkeypatch):
    provider, _ = make_provider(monkeypatch)
    with pytest.raises(AuthenticationError) as auth:
        provider.complete(cloud_request("AUTH_ERROR").messages, "mock-model")
    with pytest.raises(RateLimitError):
        provider.complete(cloud_request("RATE_LIMIT").messages, "mock-model")
    with pytest.raises(MalformedResponseError):
        provider.complete(cloud_request("MALFORMED").messages, "mock-model")
    assert "super-secret-value" not in str(auth.value)
    provider.close()


def test_timeout_crash_and_client_rate_limit(monkeypatch):
    monkeypatch.setenv("ADAPTIVEAI_TEST_KEY", "secret")

    def timeout(_request):
        raise httpx.ReadTimeout("fixture timeout")

    provider = OpenAICompatibleProvider(
        provider_config(),
        transport=httpx.MockTransport(timeout),
        resolver=public_resolver,
    )
    with pytest.raises(ProviderTimeoutError):
        provider.complete(cloud_request().messages, "mock-model")
    provider.close()

    provider, _ = make_provider(monkeypatch)
    with pytest.raises(Exception) as crash:
        provider.complete(cloud_request("CRASH").messages, "mock-model")
    assert getattr(crash.value, "kind", None) == "unavailable"
    provider.close()

    provider, _ = make_provider(monkeypatch, max_requests_per_minute=1)
    provider.complete(cloud_request().messages, "mock-model")
    with pytest.raises(RateLimitError, match="client-side"):
        provider.complete(cloud_request().messages, "mock-model")
    provider.close()


def test_gateway_scope_budget_accounting_and_unknown_pricing(monkeypatch):
    provider, _ = make_provider(monkeypatch)
    gateway = CloudGateway((provider,))
    with pytest.raises(ValueError, match="local-only"):
        gateway.complete(cloud_request(local_only=True))
    with pytest.raises(BudgetError, match="request budget"):
        gateway.complete(cloud_request(max_estimated_cost=0))
    response = gateway.complete(cloud_request())
    assert response.diagnostics.provider == "mock"
    assert response.diagnostics.estimated_cost is not None
    assert response.diagnostics.actual_cost == pytest.approx(0.000006)
    assert gateway.ledger.records[-1].usage_source == "provider"
    gateway.close()


def test_budget_reservation_prevents_concurrent_oversubscription():
    ledger = BudgetLedger(max_total=1.5)
    estimate = CostEstimate("m", "USD", 1, 1, 1.0, "fixture", "2026-11-19")
    ledger.authorize(estimate, None)
    assert ledger.reserved == 1
    with pytest.raises(BudgetError, match="total budget"):
        ledger.authorize(estimate, None)
    ledger.release(estimate.amount)
    assert ledger.reserved == 0


def test_explicit_fallback_only_after_unsupported_model(monkeypatch):
    monkeypatch.setenv("ADAPTIVEAI_TEST_KEY", "secret")
    prices = tuple(
        ModelPricing(
            model=model,
            input_per_million=1,
            output_per_million=1,
            source="test",
            retrieved_at="2026-11-19",
        )
        for model in ("primary", "fallback")
    )

    def handler(request):
        payload = json.loads(request.content)
        if payload["model"] == "primary":
            return httpx.Response(404, json={"error": "unsupported"})
        return httpx.Response(
            200,
            json={
                "id": "fallback-id",
                "model": "fallback",
                "choices": [{"message": {"content": "fallback response"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            },
        )

    config = provider_config(permitted_models=("primary", "fallback"), pricing=prices)
    provider = OpenAICompatibleProvider(
        config, transport=httpx.MockTransport(handler), resolver=public_resolver
    )
    gateway = CloudGateway((provider,))
    result = gateway.complete(cloud_request(model="primary", fallback_models=("fallback",)))
    assert result.model == "fallback"
    assert result.text == "fallback response"
    gateway.close()

    missing, _ = make_provider(monkeypatch, pricing=())
    gateway = CloudGateway((missing,))
    with pytest.raises(BudgetError, match="missing pricing"):
        gateway.complete(cloud_request())
    response = gateway.complete(cloud_request(strict_budget=False))
    assert response.diagnostics.estimated_cost is None
    gateway.close()


def make_registry(tmp_path: Path) -> ModelRegistry:
    model = tmp_path / "local.gguf"
    model.write_bytes(b"gguf")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "model_id": "local",
                        "path": str(model),
                        "family": "test",
                        "parameters": 1,
                        "quantization": "Q4",
                        "license": "Apache-2.0",
                        "context_length": 128,
                        "file_sha256": None,
                    }
                ]
            }
        )
    )
    return ModelRegistry(registry)


def test_full_client_adaptiveai_provider_response_path(tmp_path, monkeypatch):
    provider, _ = make_provider(monkeypatch)
    gateway = CloudGateway((provider,))
    manager = Mock()
    manager.status.return_value = {"healthy": True}
    registry = make_registry(tmp_path)
    config = ProductConfig(local_only=False, max_concurrency=2)
    service = ProductService(manager, registry, config, gateway)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service, config))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = AdaptiveAIClient(f"http://127.0.0.1:{server.server_port}")
    try:
        response = client.chat(
            "hello",
            model="mock-model",
            provider_scope="cloud",
            provider="mock",
            local_only=False,
            max_estimated_cost=1,
        )
        assert response["choices"][0]["message"]["content"] == "mock response"
        assert response["routing"]["provider"] == "mock"
        chunks = list(
            client.stream(
                "hello",
                model="mock-model",
                provider_scope="cloud",
                provider="mock",
                local_only=False,
                max_estimated_cost=1,
            )
        )
        assert any("mock " in str(item) for item in chunks)
        providers = httpx.get(f"http://127.0.0.1:{server.server_port}/v1/providers").json()
        assert providers["data"][0]["quality"] == "unknown"
        assert not manager.complete.called
    finally:
        server.shutdown()
        server.server_close()
        gateway.close()


def test_cli_provider_inspection_performs_no_provider_request(tmp_path, monkeypatch, capsys):
    from adaptiveai.cli import main

    config = tmp_path / "adaptiveai.toml"
    config.write_text(
        """
[adaptiveai]
local_only = true

[[adaptiveai.cloud_providers]]
provider_id = "mock"
base_url = "https://api.example.test"
api_key_env = "ADAPTIVEAI_TEST_KEY"
permitted_models = ["mock-model"]
allowed_hosts = ["api.example.test"]

[[adaptiveai.cloud_providers.pricing]]
model = "mock-model"
input_per_million = 1.0
output_per_million = 2.0
currency = "USD"
source = "test"
retrieved_at = "2026-11-19"
""".strip()
    )
    monkeypatch.setenv("ADAPTIVEAI_TEST_KEY", "secret")
    assert main(["--config", str(config), "providers", "list"]) == 0
    output = capsys.readouterr().out
    assert '"credential_available": true' in output
    assert "secret" not in output
    assert (
        main(
            [
                "--config",
                str(config),
                "providers",
                "estimate",
                "--provider",
                "mock",
                "--model",
                "mock-model",
                "--input-tokens",
                "10",
                "--max-output-tokens",
                "20",
            ]
        )
        == 0
    )
    estimate = capsys.readouterr().out
    assert '"worst_case_estimate": "0.00005"' in estimate
