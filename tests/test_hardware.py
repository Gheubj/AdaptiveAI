import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from adaptiveai.hardware import discover_hardware
from adaptiveai.hardware_routing import (
    ModelEstimate,
    RoutingConstraints,
    eligible_models,
    route_hardware_aware,
)
from adaptiveai.local_api import Phase4Service, make_handler
from adaptiveai.local_backend import (
    BackendError,
    InferenceParameters,
    LlamaCppBackend,
    LlamaCppServer,
    LocalModel,
    _parse_timings,
    load_registry,
)
from adaptiveai.phase4_experiments import quality_panel, score_answer
from adaptiveai.providers import MockCloudProvider


def test_hardware_discovery_is_non_identifying_and_bounded():
    profile = discover_hardware()
    assert profile.total_ram_bytes > 0
    assert profile.logical_cores
    assert profile.architecture
    assert "serial" not in json.dumps(profile.to_dict()).lower()


def test_registry_and_model_availability(tmp_path):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"gguf")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "model_id": "m",
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
    loaded = load_registry(registry)
    assert loaded[0].with_hash().file_sha256


def test_backend_rejects_missing_binary_and_unknown_model(tmp_path):
    with pytest.raises(BackendError):
        LlamaCppBackend(tmp_path / "missing", ())
    binary = tmp_path / "llama"
    binary.touch()
    backend = LlamaCppBackend(binary, ())
    with pytest.raises(BackendError, match="Unknown"):
        backend.infer("missing", "prompt")


def test_backend_timeout(tmp_path):
    binary = tmp_path / "llama"
    binary.touch()
    model_path = tmp_path / "model.gguf"
    model_path.touch()
    model = LocalModel("m", model_path, "test", 1, "Q4", "Apache-2.0", 128)
    backend = LlamaCppBackend(binary, (model,))
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("x", 1)):
        with pytest.raises(BackendError, match="timed out"):
            backend.infer("m", "prompt", InferenceParameters(), timeout=1)


def test_server_timeout_is_reported_as_backend_error(tmp_path):
    binary = tmp_path / "server"
    model_path = tmp_path / "model.gguf"
    binary.touch()
    model_path.touch()
    server = LlamaCppServer(binary, LocalModel("m", model_path, "test", 1, "Q4", "Apache-2.0", 128))
    server.process = Mock()
    server.process.poll.return_value = None
    with patch("httpx.stream", side_effect=httpx.ReadTimeout("late")):
        with pytest.raises(BackendError, match="timed out"):
            server.infer_stream_metrics("prompt", InferenceParameters(), timeout=1)


def test_server_reports_crashed_process(tmp_path):
    binary = tmp_path / "server"
    model_path = tmp_path / "model.gguf"
    binary.touch()
    model_path.touch()
    server = LlamaCppServer(binary, LocalModel("m", model_path, "test", 1, "Q4", "Apache-2.0", 128))
    server.process = Mock()
    server.process.poll.return_value = 9
    with pytest.raises(BackendError, match="not running"):
        server.infer("prompt", InferenceParameters())


def test_server_reports_model_load_failure(tmp_path):
    binary = tmp_path / "server"
    model_path = tmp_path / "bad.gguf"
    binary.touch()
    model_path.touch()
    server = LlamaCppServer(binary, LocalModel("m", model_path, "test", 1, "Q4", "Apache-2.0", 128))
    process = Mock()
    process.poll.return_value = 1
    process.stderr.read.return_value = "invalid model"
    with patch("subprocess.Popen", return_value=process):
        with pytest.raises(BackendError, match="invalid model"):
            server.start()


def test_memory_privacy_latency_and_cost_constraints():
    estimates = (
        ModelEstimate("local-fast", "local", 0.5, 1, 100),
        ModelEstimate("local-large", "local", 0.9, 5, 1000),
        ModelEstimate("cloud", "cloud", 1, 0.1, 0, expected_cost=0.1),
    )
    constraints = RoutingConstraints(local_only=True, available_memory_bytes=500, max_p95_latency=2)
    assert [model.model_id for model in eligible_models(estimates, constraints)] == ["local-fast"]
    decision = route_hardware_aware(estimates, constraints)
    assert decision.model_id == "local-fast"
    assert decision.provenance["provider"] == "local"


def test_no_feasible_model_and_deterministic_random():
    estimates = (ModelEstimate("m", "local", 0.5, 2, 100),)
    with pytest.raises(ValueError, match="No model"):
        route_hardware_aware(estimates, RoutingConstraints(max_p95_latency=1))
    first = route_hardware_aware(estimates, RoutingConstraints(), policy="random", seed=7)
    second = route_hardware_aware(estimates, RoutingConstraints(), policy="random", seed=7)
    assert first == second


def test_timing_parser_is_graceful():
    assert _parse_timings("unrelated") == (None, None)


def test_api_handler_factory_and_public_bind_guard():
    service = Mock()
    handler = make_handler(service)
    assert handler is not None


def test_service_enforces_local_only_and_returns_provenance():
    backend = Mock()
    backend.list_models.return_value = (
        LocalModel("local", Path("m"), "test", 1, "Q4", "Apache-2.0", 128),
    )
    estimates = (
        ModelEstimate("local", "local", 0.5, 1, 100),
        ModelEstimate("cloud", "cloud", 1, 0.1, 0),
    )
    decision = Phase4Service(backend, estimates).route({"local_only": True})
    assert decision["model"] == "local"
    assert decision["provenance"]["provider"] == "local"


def test_mock_cloud_provider_never_calls_network():
    provider = MockCloudProvider({"hello": "world"})
    with pytest.raises(RuntimeError, match="disabled"):
        provider.infer("m", "hello")
    enabled = MockCloudProvider({"hello": "world"}, enabled=True)
    assert enabled.infer("m", "hello").text == "world"


def test_quality_panel_is_frozen_and_objectively_scored():
    panel = quality_panel()
    assert panel.groupby("split").size().to_dict() == {"test": 8, "train": 8, "validation": 8}
    assert score_answer("45", "45") == 1
    assert score_answer("The answer is 45", "45") == 0
