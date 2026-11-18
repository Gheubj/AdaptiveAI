import json
import threading
from dataclasses import replace
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from pydantic import ValidationError

from adaptiveai import cli
from adaptiveai.api import ChatPayload, ProductService, make_handler
from adaptiveai.config import ProductConfig, load_product_config
from adaptiveai.lifecycle import ModelManager
from adaptiveai.local_backend import InferenceResult
from adaptiveai.product_registry import ModelRegistry
from adaptiveai.public import (
    ChatMessage,
    InferenceRequest,
    InferenceResponse,
    RoutingDiagnostics,
    RoutingMode,
)
from adaptiveai.routing_engine import ModelProfile, RoutingEngine


def profiles():
    return (
        ModelProfile(
            "fast", estimated_quality=0.4, predicted_p95_latency_seconds=0.2, memory_bytes=100
        ),
        ModelProfile(
            "strong", estimated_quality=0.8, predicted_p95_latency_seconds=1.0, memory_bytes=1000
        ),
    )


def request(**updates):
    base = InferenceRequest(messages=(ChatMessage("user", "hello"),))
    return replace(base, **updates)


def make_registry(tmp_path: Path) -> ModelRegistry:
    rows = []
    for model_id in ("fast", "strong"):
        model = tmp_path / f"{model_id}.gguf"
        model.write_bytes(b"gguf")
        rows.append(
            {
                "model_id": model_id,
                "path": str(model),
                "family": "test",
                "parameters": 1,
                "quantization": "Q4",
                "license": "Apache-2.0",
                "context_length": 128,
                "file_sha256": None,
            }
        )
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"models": rows}))
    return ModelRegistry(path)


def test_config_validation_and_toml(tmp_path):
    path = tmp_path / "adaptiveai.toml"
    path.write_text('[adaptiveai]\ndefault_routing_mode="fastest"\nport=9000\n')
    config = load_product_config(path)
    assert config.port == 9000
    assert config.default_routing_mode == "fastest"
    with pytest.raises(ValidationError, match="remote binding"):
        ProductConfig(host="0.0.0.0")
    with pytest.raises(ValidationError):
        ProductConfig(max_concurrency=0)


def test_registry_availability_and_duplicate_guard(tmp_path):
    registry = make_registry(tmp_path)
    assert all(status.available for status in registry.inspect())
    assert registry.get("fast").model_id == "fast"
    with pytest.raises(ValueError, match="Unknown"):
        registry.get("missing")


def test_routing_modes_constraints_and_explicit_selection():
    router = RoutingEngine(profiles(), balanced_latency_weight=0.15)
    assert router.select(request(routing_mode=RoutingMode.FASTEST)).selected_model == "fast"
    assert router.select(request(routing_mode=RoutingMode.QUALITY)).selected_model == "strong"
    assert router.select(request(routing_mode=RoutingMode.BALANCED)).selected_model == "strong"
    assert (
        router.select(request(routing_mode=RoutingMode.HARDWARE_AWARE)).selected_model == "strong"
    )
    assert router.select(request(model="fast")).reason == "explicit model selection"
    constrained = request(routing_mode=RoutingMode.QUALITY, available_memory_bytes=500)
    assert router.select(constrained).selected_model == "fast"
    with pytest.raises(ValueError, match="violates constraints"):
        router.select(request(model="strong", available_memory_bytes=500))


def test_missing_profiles_are_explicit_errors():
    router = RoutingEngine((ModelProfile("m"),))
    with pytest.raises(ValueError, match="latency profiles"):
        router.select(request(routing_mode=RoutingMode.FASTEST))
    with pytest.raises(ValueError, match="quality estimates"):
        router.select(request(routing_mode=RoutingMode.QUALITY))


def test_lifecycle_stickiness_and_explicit_model_override(tmp_path):
    binary = tmp_path / "llama-server"
    binary.touch()
    registry = make_registry(tmp_path)
    router = RoutingEngine(profiles(), balanced_latency_weight=0.15)
    manager = ModelManager(registry, router, binary, switch_hysteresis_seconds=3)
    manager.current_model = "fast"
    decision = manager._apply_stickiness(
        request(routing_mode=RoutingMode.BALANCED),
        router.select(request(routing_mode=RoutingMode.BALANCED)),
    )
    assert decision.selected_model == "fast"
    assert decision.fallback_reason
    explicit = request(model="strong", routing_mode=RoutingMode.BALANCED)
    assert manager._apply_stickiness(explicit, router.select(explicit)).selected_model == "strong"


def test_lifecycle_completion_and_cleanup(tmp_path):
    binary = tmp_path / "llama-server"
    binary.touch()
    registry = make_registry(tmp_path)
    manager = ModelManager(registry, RoutingEngine(profiles()), binary)
    fake_server = Mock()
    fake_server.process.poll.return_value = None
    fake_server.start.return_value = 0.2
    fake_server.infer.return_value = InferenceResult("id", "fast", "ok", 0.1, 2, 1, 10, "test", "")
    with patch("adaptiveai.lifecycle.LlamaCppServer", return_value=fake_server):
        result = manager.complete(request(model="fast"))
        assert result.text == "ok"
        assert result.diagnostics.loading_seconds == 0.2
        manager.shutdown()
    fake_server.stop.assert_called()


def _api_server(tmp_path):
    registry = make_registry(tmp_path)
    manager = Mock()
    manager.status.return_value = {"healthy": True, "current_model": None}
    diagnostics = RoutingDiagnostics("fast", "fastest", "test", ("fast",))
    manager.complete.return_value = InferenceResponse("id", "fast", "hello", 3, 1, diagnostics)
    manager.stream.return_value = iter(
        [
            {"type": "content", "request_id": "id", "model": "fast", "content": "hel"},
            {"type": "content", "request_id": "id", "model": "fast", "content": "lo"},
            {
                "type": "done",
                "request_id": "id",
                "model": "fast",
                "diagnostics": diagnostics,
            },
        ]
    )
    config = ProductConfig(max_concurrency=2)
    service = ProductService(manager, registry, config)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service, config))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, manager


def test_api_health_models_chat_invalid_and_streaming(tmp_path):
    server, manager = _api_server(tmp_path)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert httpx.get(f"{base}/health").status_code == 200
        assert len(httpx.get(f"{base}/v1/models").json()["data"]) == 2
        payload = {"messages": [{"role": "user", "content": "hi"}], "model": "fast"}
        response = httpx.post(f"{base}/v1/chat/completions", json=payload)
        assert response.status_code == 200
        assert response.json()["choices"][0]["message"]["content"] == "hello"
        invalid = httpx.post(f"{base}/v1/chat/completions", json={"messages": []})
        assert invalid.status_code == 400
        with httpx.stream(
            "POST", f"{base}/v1/chat/completions", json={**payload, "stream": True}
        ) as streamed:
            body = "\n".join(streamed.iter_lines())
        assert "chat.completion.chunk" in body
        assert "data: [DONE]" in body
        assert manager.complete.called
    finally:
        server.shutdown()
        server.server_close()


def test_chat_payload_rejects_unsupported_fields_and_unsafe_values():
    with pytest.raises(ValidationError):
        ChatPayload.model_validate(
            {"messages": [{"role": "user", "content": "x"}], "temperature": 5}
        )
    with pytest.raises(ValidationError):
        ChatPayload.model_validate(
            {"messages": [{"role": "user", "content": "x"}], "unknown": True}
        )


def test_entrypoint_explains_missing_research_extra():
    missing = ModuleNotFoundError("missing")
    missing.name = "pandas"
    with patch("adaptiveai.cli.main", side_effect=missing):
        with pytest.raises(SystemExit, match="research dependency.*research"):
            cli.entrypoint()
