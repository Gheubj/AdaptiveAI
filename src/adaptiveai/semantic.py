from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from torch import nn

ENCODER_ID = "sentence-transformers/all-MiniLM-L6-v2"
ENCODER_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"


def cache_semantic_embeddings(
    queries_path: Path, output: Path, *, batch_size: int = 256
) -> dict[str, object]:
    from sentence_transformers import SentenceTransformer

    queries = pd.read_parquet(queries_path, columns=["query_id", "origin_query", "prompt"])
    texts = queries.origin_query.fillna(queries.prompt).fillna("").astype(str).tolist()
    model = SentenceTransformer(ENCODER_ID, revision=ENCODER_REVISION)
    model.max_seq_length = 128
    started = time.perf_counter()
    embeddings = model.encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True
    )
    elapsed = time.perf_counter() - started
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output, query_ids=queries.query_id.to_numpy(), embeddings=embeddings.astype(np.float32)
    )
    metadata: dict[str, object] = {
        "encoder_id": ENCODER_ID,
        "revision": ENCODER_REVISION,
        "license": "Apache-2.0",
        "dimension": int(embeddings.shape[1]),
        "max_sequence_length": 128,
        "queries": len(queries),
        "seconds": elapsed,
        "throughput_qps": len(queries) / elapsed,
        "cache_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    return metadata


def load_embedding_cache(path: Path) -> tuple[dict[str, int], np.ndarray]:
    # Query ids are an object array; this file is a trusted, locally generated cache.
    with np.load(path, allow_pickle=True) as data:
        ids = data["query_ids"].astype(str)
        embeddings = data["embeddings"].copy()
    return {query_id: index for index, query_id in enumerate(ids)}, embeddings


class SemanticMLP(nn.Module):
    def __init__(self, dimension: int, models: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dimension, hidden), nn.ReLU(), nn.Dropout(0.1), nn.Linear(hidden, models)
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


class SemanticShared(nn.Module):
    def __init__(self, dimension: int, models: int, hidden: int = 64, model_dim: int = 32):
        super().__init__()
        self.projection = nn.Linear(dimension, model_dim)
        self.models = nn.Embedding(models, model_dim)
        self.head = nn.Sequential(nn.Linear(model_dim * 3, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        query = self.projection(features)
        model = self.models.weight
        queries = query[:, None, :].expand(-1, len(model), -1)
        models = model[None, :, :].expand(len(query), -1, -1)
        return self.head(torch.cat([queries, models, queries * models], -1)).squeeze(-1)


class BudgetGate(nn.Module):
    def __init__(self, dimension: int, models: int, hidden: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dimension + models * 2, hidden), nn.ReLU(), nn.Linear(hidden, models)
        )

    def forward(
        self, features: torch.Tensor, quality: torch.Tensor, costs: torch.Tensor
    ) -> torch.Tensor:
        return self.net(torch.cat([features, quality, costs.expand(len(features), -1)], dim=1))


def fit_semantic_logistic(
    features: np.ndarray, labels: np.ndarray, seed: int
) -> list[LogisticRegression | float]:
    result: list[LogisticRegression | float] = []
    for column in range(labels.shape[1]):
        observed = np.isfinite(labels[:, column])
        targets = (labels[observed, column] >= 1).astype(int)
        if len(np.unique(targets)) == 1:
            result.append(float(targets[0]))
        else:
            model = LogisticRegression(C=1, max_iter=300, random_state=seed)
            model.fit(features[observed], targets)
            result.append(model)
    return result


def logistic_predict(models: list[LogisticRegression | float], features: np.ndarray) -> np.ndarray:
    return np.column_stack(
        [
            np.full(len(features), model)
            if isinstance(model, float)
            else model.predict_proba(features)[:, 1]
            for model in models
        ]
    )


def train_semantic_torch(
    model: nn.Module,
    train_features: np.ndarray,
    train_labels: np.ndarray,
    validation_features: np.ndarray,
    validation_labels: np.ndarray,
    seed: int,
    epochs: int = 30,
) -> dict[str, float | int]:
    torch.manual_seed(seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-5)
    x_train, y_train = torch.tensor(train_features), torch.tensor(train_labels)
    x_validation, y_validation = torch.tensor(validation_features), torch.tensor(validation_labels)
    best, state, stale = float("inf"), None, 0
    started = time.perf_counter()
    for epoch in range(epochs):
        model.train()
        generator = torch.Generator().manual_seed(seed + epoch)
        for indices in torch.randperm(len(x_train), generator=generator).split(256):
            logits = model(x_train[indices])
            target = (y_train[indices] >= 1).float()
            mask = torch.isfinite(y_train[indices])
            loss = nn.functional.binary_cross_entropy_with_logits(logits[mask], target[mask])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            logits = model(x_validation)
            target = (y_validation >= 1).float()
            mask = torch.isfinite(y_validation)
            validation_loss = float(
                nn.functional.binary_cross_entropy_with_logits(logits[mask], target[mask])
            )
        if validation_loss < best - 1e-5:
            best = validation_loss
            state = {name: value.detach().clone() for name, value in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
        if stale >= 3:
            break
    assert state is not None
    model.load_state_dict(state)
    return {
        "seconds": time.perf_counter() - started,
        "epochs": epoch + 1,
        "validation_loss": best,
    }


def predict_torch(model: nn.Module, features: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(torch.tensor(features))).numpy()


def confidence_fallback(probabilities: np.ndarray, best_model: int, threshold: float) -> np.ndarray:
    order = np.sort(probabilities, axis=1)
    margin = order[:, -1] - order[:, -2]
    chosen = probabilities.argmax(1)
    chosen[margin < threshold] = best_model
    return chosen


def disagreement_fallback(first: np.ndarray, second: np.ndarray, best_model: int) -> np.ndarray:
    chosen = first.argmax(1)
    chosen[chosen != second.argmax(1)] = best_model
    return chosen


def budget_violation(selections: np.ndarray, costs: np.ndarray, budget: float) -> float:
    return max(0.0, float(costs[selections].mean()) - budget)


def train_budget_gate(
    features: np.ndarray,
    quality_predictions: np.ndarray,
    labels: np.ndarray,
    costs: np.ndarray,
    budget: float,
    seed: int,
    epochs: int = 40,
) -> tuple[BudgetGate, dict[str, list[float]]]:
    """Optimize expected observed success with a primal-dual mean-cost constraint."""
    torch.manual_seed(seed)
    model = BudgetGate(features.shape[1], labels.shape[1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-5)
    x = torch.tensor(features)
    predictions = torch.tensor(quality_predictions)
    targets = torch.tensor(np.nan_to_num(labels, nan=0.0) >= 1, dtype=torch.float32)
    cost = torch.tensor(costs)[None, :]
    dual = 0.0
    history: dict[str, list[float]] = {"quality": [], "cost": [], "dual": []}
    for epoch in range(epochs):
        generator = torch.Generator().manual_seed(seed + epoch)
        for indices in torch.randperm(len(x), generator=generator).split(256):
            policy = torch.softmax(model(x[indices], predictions[indices], cost), dim=1)
            expected_quality = (policy * targets[indices]).sum(1).mean()
            expected_cost = (policy * cost).sum(1).mean()
            loss = -expected_quality + dual * (expected_cost - budget)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            dual = max(0.0, dual + 0.5 * float(expected_cost.detach() - budget))
        history["quality"].append(float(expected_quality.detach()))
        history["cost"].append(float(expected_cost.detach()))
        history["dual"].append(dual)
    return model, history


def deterministic_budget_selection(
    probabilities: np.ndarray, costs: np.ndarray, budget: float
) -> tuple[np.ndarray, float]:
    candidates = np.concatenate(([0.0], np.logspace(-4, 4, 161)))
    feasible: list[tuple[float, float, np.ndarray]] = []
    for penalty in candidates:
        selection = (probabilities - penalty * costs[None, :]).argmax(1)
        mean_cost = float(costs[selection].mean())
        if mean_cost <= budget * 1.005:
            feasible.append((penalty, mean_cost, selection))
    if not feasible:
        cheapest = int(costs.argmin())
        return np.full(len(probabilities), cheapest), float("inf")
    penalty, _, selection = min(feasible, key=lambda item: item[0])
    return selection, float(penalty)
