import os
from pathlib import Path

import pytest

from adaptiveai.lifecycle import ModelManager
from adaptiveai.product_registry import ModelRegistry
from adaptiveai.public import ChatMessage, InferenceRequest, RoutingMode
from adaptiveai.routing_engine import RoutingEngine, load_model_profiles


@pytest.mark.real_local
@pytest.mark.skipif(
    os.getenv("ADAPTIVEAI_REAL_LOCAL") != "1",
    reason="set ADAPTIVEAI_REAL_LOCAL=1 to run local llama.cpp smoke test",
)
def test_real_local_start_request_response_and_cleanup():
    registry_path = Path("data/local_model_registry.json")
    registry = ModelRegistry(registry_path)
    profiles = load_model_profiles(
        registry_path.with_name("local_model_profiles.json"),
        tuple(model.model_id for model in registry.models()),
    )
    manager = ModelManager(
        registry, RoutingEngine(profiles), Path("vendor/llama.cpp/build/bin/llama-server")
    )
    try:
        result = manager.complete(
            InferenceRequest(
                messages=(ChatMessage("user", "Reply with exactly: ready"),),
                routing_mode=RoutingMode.FASTEST,
                max_tokens=16,
            )
        )
        assert result.text.strip()
        assert manager.status()["healthy"]
    finally:
        manager.shutdown()
    assert manager.current_model is None
