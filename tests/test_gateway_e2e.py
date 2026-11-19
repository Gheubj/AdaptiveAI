import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock

import pytest

from adaptiveai.api import ProductService, make_handler
from adaptiveai.auto_routing import AutoCandidate, AutoEvidence, AutoRoutingPolicy, TaskCategory
from adaptiveai.client import AdaptiveAIClient
from adaptiveai.cloud import (
    AuthenticationError,
    BudgetError,
    CloudProviderConfig,
    InterruptedStreamError,
    InvalidProviderRequestError,
    MalformedResponseError,
    ModelPricing,
    OpenAICompatibleProvider,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
    UnsupportedModelError,
)
from adaptiveai.cloud_gateway import CloudGateway
from adaptiveai.config import ProductConfig
from adaptiveai.product_registry import ModelRegistry
from adaptiveai.public import ChatMessage, InferenceRequest, ProviderScope
from adaptiveai.test_provider import make_test_provider


def loopback_resolver(*_args, **_kwargs):
    return [(2, 1, 6, "", ("127.0.0.1", 80))]


def make_registry(tmp_path: Path):
    model = tmp_path / "local.gguf"
    model.write_bytes(b"gguf")
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "model_id": "local",
                        "path": str(model),
                        "family": "fixture",
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
    return ModelRegistry(path)


@pytest.fixture
def local_provider(monkeypatch):
    monkeypatch.setenv("ADAPTIVEAI_E2E_KEY", "local-test-key")
    server = make_test_provider()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = CloudProviderConfig(
        provider_id="local-e2e",
        deployment_id="localhost-fixture",
        base_url=f"http://127.0.0.1:{server.server_port}",
        api_key_env="ADAPTIVEAI_E2E_KEY",
        permitted_models=("local-e2e", "fallback", "missing"),
        hosted_mode=False,
        allow_localhost=True,
        timeout_seconds=0.05,
        connect_timeout_seconds=0.05,
        max_response_bytes=1024,
        pricing=(
            ModelPricing(
                model="local-e2e",
                input_per_million=1,
                output_per_million=2,
                source="synthetic local fixture",
                retrieved_at="2026-11-19",
            ),
            ModelPricing(
                model="fallback",
                input_per_million=1,
                output_per_million=2,
                source="synthetic local fixture",
                retrieved_at="2026-11-19",
            ),
            ModelPricing(
                model="missing",
                input_per_million=1,
                output_per_million=2,
                source="synthetic local fixture",
                retrieved_at="2026-11-19",
            ),
        ),
    )
    adapter = OpenAICompatibleProvider(config, resolver=loopback_resolver)
    yield server, adapter
    adapter.close()
    server.shutdown()
    server.server_close()


def req(text="hello", **updates):
    values = {
        "messages": (ChatMessage("user", text),),
        "model": "local-e2e",
        "provider": "local-e2e",
        "provider_scope": ProviderScope.CLOUD,
        "local_only": False,
        "max_tokens": 8,
        "max_estimated_cost": 1,
    }
    values.update(updates)
    return InferenceRequest(**values)


def test_real_http_provider_protocol_and_errors(local_provider, monkeypatch):
    _server, adapter = local_provider
    assert adapter.discover_models() == ("local-e2e", "fallback")
    assert adapter.complete(req().messages, "local-e2e").text == "local response"
    chunks = list(adapter.stream(req().messages, "local-e2e"))
    assert "".join(item.get("content", "") for item in chunks) == "local response"
    with pytest.raises(RateLimitError):
        adapter.complete(req("RATE_LIMIT").messages, "local-e2e")
    with pytest.raises(UnsupportedModelError):
        adapter.complete(req().messages, "missing")
    with pytest.raises(ProviderUnavailableError):
        adapter.complete(req("UNAVAILABLE").messages, "local-e2e")
    with pytest.raises(InvalidProviderRequestError):
        adapter.complete(req("INVALID").messages, "local-e2e")
    with pytest.raises(MalformedResponseError):
        adapter.complete(req("MALFORMED").messages, "local-e2e")
    with pytest.raises(MalformedResponseError, match="response limit"):
        adapter.complete(req("OVERSIZED").messages, "local-e2e")
    with pytest.raises(ProviderTimeoutError):
        adapter.complete(req("READ_TIMEOUT").messages, "local-e2e")
    with pytest.raises(InterruptedStreamError):
        list(adapter.stream(req("INTERRUPTED").messages, "local-e2e"))
    without_usage = adapter.complete(req("NO_USAGE").messages, "local-e2e")
    assert without_usage.usage.source == "unreported"
    monkeypatch.setenv("ADAPTIVEAI_E2E_KEY", "wrong-secret")
    with pytest.raises(AuthenticationError) as error:
        adapter.complete(req().messages, "local-e2e")
    assert "wrong-secret" not in str(error.value)


def test_budget_local_only_allowlist_fallback_and_cancellation(local_provider):
    _server, adapter = local_provider
    gateway = CloudGateway((adapter,))
    with pytest.raises(BudgetError):
        gateway.complete(req(max_estimated_cost=0))
    with pytest.raises(ValueError, match="local-only"):
        gateway.complete(req(local_only=True))
    with pytest.raises(ValueError, match="exactly one"):
        gateway.complete(req(provider_allowlist=("other",), provider=None))
    fallback = gateway.complete(req(model="missing", fallback_models=("fallback",)))
    assert fallback.model == "fallback"
    stream = gateway.stream(req())
    next(stream)
    stream.close()
    assert gateway.ledger.records[-1].status == "interrupted"
    assert gateway.ledger.reserved == pytest.approx(0)


def test_full_client_gateway_provider_e2e_and_auto(tmp_path, local_provider):
    _provider_server, adapter = local_provider
    gateway = CloudGateway((adapter,))
    evidence = AutoEvidence(
        evidence_id="synthetic-e2e",
        category=TaskCategory.CODING,
        metric="synthetic_accuracy",
        value=1,
        comparability_group="single-not-comparative",
        provenance="synthetic fixture",
    )
    candidate = AutoCandidate(
        candidate_id="e2e-cloud",
        provider="local-e2e",
        deployment="localhost-fixture",
        model="local-e2e",
        input_per_million=1,
        output_per_million=2,
        context_tokens=4096,
        evidence=(evidence,),
    )
    router = AutoRoutingPolicy(
        (candidate,), default_candidate="e2e-cloud", uncertainty_policy="default"
    )
    manager = Mock()
    manager.status.return_value = {"healthy": True}
    registry = make_registry(tmp_path)
    config = ProductConfig(local_only=False, max_concurrency=2)
    service = ProductService(manager, registry, config, gateway, router)
    api = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service, config))
    thread = threading.Thread(target=api.serve_forever, daemon=True)
    thread.start()
    client = AdaptiveAIClient(f"http://127.0.0.1:{api.server_port}")
    try:
        manual = client.chat(
            "hello",
            model="local-e2e",
            provider="local-e2e",
            provider_scope="cloud",
            local_only=False,
            max_estimated_cost=1,
        )
        assert manual["choices"][0]["message"]["content"] == "local response"
        auto = client.chat(
            "Debug Python code",
            model="auto",
            routing_mode="auto",
            provider_scope="hybrid",
            local_only=False,
            max_estimated_cost=1,
        )
        assert auto["routing"]["explanation"]["selected_candidate"] == "e2e-cloud"
        explanation = client.route_explain("Debug Python code")
        assert explanation["status"] == "SELECTED"
        streamed = list(
            client.stream(
                "hello",
                model="local-e2e",
                provider="local-e2e",
                provider_scope="cloud",
                local_only=False,
                max_estimated_cost=1,
            )
        )
        assert any("local " in str(item) for item in streamed)
        assert not manager.complete.called
    finally:
        api.shutdown()
        api.server_close()
        gateway.close()
