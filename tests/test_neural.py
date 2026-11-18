from pathlib import Path

import numpy as np
import torch

from adaptiveai.neural import (
    QueryMatrixDataset,
    SharedModelEmbeddingRouter,
    SparseNeuralRouter,
    TrainableGatingNetwork,
    calibration_metrics,
    checkpoint_bytes,
    collate_queries,
    fit_temperature,
    hash_tokens,
    masked_bce,
    set_deterministic,
)


def test_dataset_collation_and_missing_mask() -> None:
    dataset = QueryMatrixDataset(
        ["q"], ["hello world"], np.array([[1.0, np.nan]]), ["d"], buckets=50
    )
    batch = collate_queries([dataset[0]])
    assert len(batch["tokens"]) == 2
    logits = torch.zeros((1, 2))
    assert torch.isfinite(masked_bce(logits, batch["labels"]))


def test_all_architecture_forward_shapes() -> None:
    batch = collate_queries(
        [{"query_id": "q", "tokens": [1, 2], "labels": np.array([1.0, 0.0]), "dataset": "d"}]
    )
    sparse = SparseNeuralRouter(20, 2, 4, 8, 0)
    shared = SharedModelEmbeddingRouter(20, 2, 4, 8, 0)
    assert sparse(batch["tokens"], batch["offsets"]).shape == (1, 2)
    assert shared(batch["tokens"], batch["offsets"]).shape == (1, 2)
    gate = TrainableGatingNetwork(4, 2, 8)
    assert gate(
        shared.encode(batch["tokens"], batch["offsets"]),
        torch.full((1, 2), 0.5),
        torch.zeros((1, 2)),
    ).shape == (1, 2)


def test_determinism_checkpoint_and_calibration(tmp_path: Path) -> None:
    set_deterministic(7)
    first = SparseNeuralRouter(20, 2, 4, 8, 0)
    set_deterministic(7)
    second = SparseNeuralRouter(20, 2, 4, 8, 0)
    assert checkpoint_bytes(first) == checkpoint_bytes(second)
    path = tmp_path / "model.pt"
    path.write_bytes(checkpoint_bytes(first))
    restored = SparseNeuralRouter(20, 2, 4, 8, 0)
    restored.load_state_dict(torch.load(path, weights_only=True))
    assert checkpoint_bytes(first) == checkpoint_bytes(restored)
    logits = np.array([[0.0, 1.0], [-1.0, 2.0]])
    labels = np.array([[0.0, 1.0], [0.0, 1.0]])
    temperature = fit_temperature(logits, labels)
    assert temperature > 0
    metrics = calibration_metrics(1 / (1 + np.exp(-logits / temperature)), labels)
    assert 0 <= metrics["ece"] <= 1


def test_hash_tokens_stable() -> None:
    assert hash_tokens("Same text", 100) == hash_tokens("Same text", 100)
