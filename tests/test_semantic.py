import json
from pathlib import Path

import numpy as np
import pytest
import torch

from adaptiveai.phase36_audit import _bootstrap_difference
from adaptiveai.semantic import (
    ENCODER_REVISION,
    SemanticMLP,
    budget_violation,
    confidence_fallback,
    deterministic_budget_selection,
    disagreement_fallback,
    fit_semantic_logistic,
    load_embedding_cache,
    logistic_predict,
    predict_torch,
    train_semantic_torch,
)


def test_embedding_cache_and_revision(tmp_path):
    path = tmp_path / "cache.npz"
    np.savez(path, query_ids=np.array(["a", "b"], dtype=object), embeddings=np.eye(2))
    lookup, embeddings = load_embedding_cache(path)
    assert lookup == {"a": 0, "b": 1}
    assert embeddings.shape == (2, 2)
    assert len(ENCODER_REVISION) == 40


def test_feature_prediction_is_deterministic():
    torch.manual_seed(7)
    model = SemanticMLP(3, 2)
    features = np.ones((4, 3), dtype=np.float32)
    assert np.array_equal(predict_torch(model, features), predict_torch(model, features))


def test_fallback_policies_do_not_mutate_probabilities():
    first = np.array([[0.5, 0.49], [0.2, 0.8]])
    second = np.array([[0.1, 0.9], [0.3, 0.7]])
    original = first.copy()
    assert confidence_fallback(first, 1, 0.1).tolist() == [1, 1]
    assert disagreement_fallback(first, second, 0).tolist() == [0, 1]
    assert np.array_equal(first, original)


def test_budget_selector_and_violation():
    probabilities = np.array([[0.8, 0.7], [0.8, 0.7]])
    costs = np.array([1.0, 0.1])
    selection, penalty = deterministic_budget_selection(probabilities, costs, 0.2)
    assert selection.tolist() == [1, 1]
    assert penalty > 0
    assert budget_violation(selection, costs, 0.2) == 0
    assert budget_violation(np.array([0, 0]), costs, 0.2) == 0.8


def test_embedding_metadata_matches_cache():
    metadata_path = Path("data/processed/minilm_embeddings.json")
    if not metadata_path.exists():
        pytest.skip("optional MiniLM embedding metadata cache is not distributed")
    metadata = json.loads(metadata_path.read_text())
    assert metadata["revision"] == ENCODER_REVISION
    assert metadata["dimension"] == 384


def test_logistic_handles_missing_and_constant_labels():
    features = np.array([[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]], dtype=np.float32)
    labels = np.array([[1.0, 0.0], [0.0, np.nan], [1.0, 0.0]], dtype=np.float32)
    models = fit_semantic_logistic(features, labels, 7)
    prediction = logistic_predict(models, features)
    assert prediction.shape == labels.shape
    assert np.array_equal(prediction[:, 1], np.zeros(3))


def test_semantic_training_and_checkpoint_round_trip(tmp_path):
    rng = np.random.default_rng(7)
    features = rng.normal(size=(20, 4)).astype(np.float32)
    labels = (features[:, :2] > 0).astype(np.float32)
    model = SemanticMLP(4, 2, hidden=4)
    result = train_semantic_torch(
        model, features[:16], labels[:16], features[16:], labels[16:], 7, 2
    )
    checkpoint = tmp_path / "model.pt"
    torch.save(model.state_dict(), checkpoint)
    loaded = SemanticMLP(4, 2, hidden=4)
    loaded.load_state_dict(torch.load(checkpoint, weights_only=True))
    assert np.array_equal(predict_torch(model, features), predict_torch(loaded, features))
    assert result["epochs"] <= 2


def test_paired_bootstrap_direction():
    first = __import__("pandas").DataFrame({"query_id": ["a", "b"], "success": [1.0, 1.0]})
    second = __import__("pandas").DataFrame({"query_id": ["a", "b"], "success": [0.0, 1.0]})
    difference, low, high = _bootstrap_difference(first, second, samples=100)
    assert difference == 0.5
    assert 0 <= low <= high <= 1
