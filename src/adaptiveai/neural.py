from __future__ import annotations

import hashlib
import io
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from adaptiveai.benchmark import _complete_queries, _load_panel
from adaptiveai.protocol import LIGHTWEIGHT20, PROPRIETARY8


def set_deterministic(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def hash_tokens(text: str, buckets: int) -> list[int]:
    tokens = text.lower().split() or ["<empty>"]
    return [
        int.from_bytes(hashlib.blake2b(t.encode(), digest_size=8).digest(), "big") % buckets
        for t in tokens
    ]


class QueryMatrixDataset(Dataset):
    def __init__(
        self,
        ids: list[str],
        texts: list[str],
        labels: np.ndarray,
        datasets: list[str],
        *,
        buckets: int,
    ):
        self.ids, self.texts, self.labels, self.datasets, self.buckets = (
            ids,
            texts,
            labels,
            datasets,
            buckets,
        )

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return {
            "query_id": self.ids[index],
            "tokens": hash_tokens(self.texts[index], self.buckets),
            "labels": self.labels[index],
            "dataset": self.datasets[index],
        }


def collate_queries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = [len(r["tokens"]) for r in rows]
    offsets = torch.tensor(np.cumsum([0] + lengths[:-1]), dtype=torch.long)
    return {
        "tokens": torch.tensor([x for r in rows for x in r["tokens"]], dtype=torch.long),
        "offsets": offsets,
        "labels": torch.tensor(np.stack([r["labels"] for r in rows]), dtype=torch.float32),
        "query_ids": [r["query_id"] for r in rows],
        "datasets": [r["dataset"] for r in rows],
    }


class SparseNeuralRouter(nn.Module):
    def __init__(
        self, buckets: int, models: int, embedding_dim: int, hidden_dim: int, dropout: float
    ):
        super().__init__()
        self.encoder = nn.EmbeddingBag(buckets, embedding_dim, mode="mean")
        self.head = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, models),
        )

    def encode(self, tokens: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        return self.encoder(tokens, offsets)

    def forward(self, tokens: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        return self.head(self.encode(tokens, offsets))


class SharedModelEmbeddingRouter(nn.Module):
    def __init__(
        self, buckets: int, models: int, embedding_dim: int, hidden_dim: int, dropout: float
    ):
        super().__init__()
        self.encoder = nn.EmbeddingBag(buckets, embedding_dim, mode="mean")
        self.model_embeddings = nn.Embedding(models, embedding_dim)
        self.scorer = nn.Sequential(
            nn.Linear(embedding_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def encode(self, tokens: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        return self.encoder(tokens, offsets)

    def forward(self, tokens: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        h = self.encode(tokens, offsets)
        e = self.model_embeddings.weight
        hh = h[:, None, :].expand(-1, len(e), -1)
        ee = e[None, :, :].expand(len(h), -1, -1)
        return self.scorer(torch.cat([hh, ee, hh * ee], dim=-1)).squeeze(-1)


class TrainableGatingNetwork(nn.Module):
    """Trainable policy over frozen quality predictions and shared query representations."""

    def __init__(self, query_dim: int, models: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(query_dim + models * 2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, models)
        )

    def forward(
        self, query: torch.Tensor, quality: torch.Tensor, costs: torch.Tensor
    ) -> torch.Tensor:
        return self.net(torch.cat([query, quality, costs.expand(len(query), -1)], dim=1))


@dataclass(frozen=True)
class NeuralConfig:
    pool: str = "proprietary8"
    buckets: int = 20_000
    embedding_dim: int = 32
    hidden_dim: int = 64
    dropout: float = 0.1
    batch_size: int = 128
    learning_rate: float = 0.003
    weight_decay: float = 1e-5
    epochs: int = 12
    patience: int = 2
    cost_lambda: float = 1.0
    seed: int = 3407


def load_neural_data(
    processed: Path, config: NeuralConfig
) -> tuple[dict[str, QueryMatrixDataset], tuple[str, ...], np.ndarray, pd.DataFrame]:
    names = LIGHTWEIGHT20 if config.pool == "lightweight20" else PROPRIETARY8
    panel, models = _load_panel(processed, names, "mean")
    splits = pd.read_parquet(
        processed / "data_splits.parquet", columns=["query_id", "duplicate_group_id", "split"]
    )
    queries = pd.read_parquet(
        processed / "queries.parquet", columns=["query_id", "dataset", "origin_query", "prompt"]
    )
    complete = _complete_queries(panel, models)
    panel = panel[panel.query_id.isin(complete)]
    quality = panel.pivot(index="query_id", columns="model_id", values="quality_score").reindex(
        columns=models
    )
    costs = (
        panel[panel.query_id.isin(set(splits.loc[splits.split == "train", "query_id"]))]
        .groupby("model_id")
        .historical_cost_usd.mean()
        .reindex(models)
        .fillna(0)
        .to_numpy(np.float32)
    )
    q = queries.set_index("query_id")
    split_lookup = splits.set_index("query_id")
    result = {}
    for split in ("train", "validation", "test", "ood_test"):
        ids = sorted(set(quality.index) & set(splits.loc[splits.split == split, "query_id"]))
        texts = [
            str(q.loc[i].origin_query if pd.notna(q.loc[i].origin_query) else q.loc[i].prompt or "")
            for i in ids
        ]
        result[split] = QueryMatrixDataset(
            ids,
            texts,
            quality.loc[ids].to_numpy(np.float32),
            [str(q.loc[i].dataset) for i in ids],
            buckets=config.buckets,
        )
    return result, models, costs, split_lookup


def masked_bce(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    mask = torch.isfinite(labels)
    targets = (labels >= 1).float()
    loss = nn.functional.binary_cross_entropy_with_logits(
        logits[mask], targets[mask], reduction="none"
    )
    weights = mask.sum(1).clamp_min(1).reciprocal().repeat_interleave(mask.sum(1))
    return (loss * weights).sum() / len(labels)


def masked_mse(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    mask = torch.isfinite(labels)
    error = (torch.sigmoid(logits) - labels).square()
    return (error.masked_fill(~mask, 0).sum(1) / mask.sum(1).clamp_min(1)).mean()


def _loader(dataset: QueryMatrixDataset, config: NeuralConfig, shuffle: bool) -> DataLoader:
    generator = torch.Generator().manual_seed(config.seed)
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=shuffle,
        collate_fn=collate_queries,
        generator=generator,
    )


def train_predictor(
    model: nn.Module,
    data: dict[str, QueryMatrixDataset],
    config: NeuralConfig,
    *,
    objective: str = "bce",
) -> dict[str, Any]:
    set_deterministic(config.seed)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    loss_fn = masked_bce if objective == "bce" else masked_mse
    best, best_state, stale, history = float("inf"), None, 0, []
    started = time.perf_counter()
    for epoch in range(config.epochs):
        model.train()
        train_losses = []
        for batch in _loader(data["train"], config, True):
            optimizer.zero_grad()
            loss = loss_fn(model(batch["tokens"], batch["offsets"]), batch["labels"])
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss.detach()))
        model.eval()
        validation = []
        with torch.no_grad():
            for batch in _loader(data["validation"], config, False):
                validation.append(
                    float(loss_fn(model(batch["tokens"], batch["offsets"]), batch["labels"]))
                )
        val = float(np.mean(validation))
        history.append(
            {"epoch": epoch, "train_loss": float(np.mean(train_losses)), "validation_loss": val}
        )
        if val < best - 1e-5:
            best, best_state, stale = (
                val,
                {k: v.detach().clone() for k, v in model.state_dict().items()},
                0,
            )
        else:
            stale += 1
        if stale >= config.patience:
            break
    assert best_state is not None
    model.load_state_dict(best_state)
    return {
        "history": history,
        "training_seconds": time.perf_counter() - started,
        "best_validation_loss": best,
    }


def predict(
    model: nn.Module, dataset: QueryMatrixDataset, config: NeuralConfig
) -> tuple[np.ndarray, np.ndarray, float]:
    model.eval()
    logits, labels = [], []
    started = time.perf_counter()
    with torch.no_grad():
        for batch in _loader(dataset, config, False):
            logits.append(model(batch["tokens"], batch["offsets"]).numpy())
            labels.append(batch["labels"].numpy())
    elapsed = time.perf_counter() - started
    return np.concatenate(logits), np.concatenate(labels), elapsed


def fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    mask = np.isfinite(labels)
    x = torch.tensor(logits[mask])
    y = torch.tensor((labels[mask] >= 1).astype(np.float32))
    raw = torch.tensor(0.0, requires_grad=True)
    optimizer = torch.optim.LBFGS([raw], max_iter=50, line_search_fn="strong_wolfe")

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        loss = nn.functional.binary_cross_entropy_with_logits(x / raw.exp(), y)
        loss.backward()
        return loss

    optimizer.step(closure)
    return float(raw.exp().detach().clamp(0.05, 20))


def calibration_metrics(
    probabilities: np.ndarray, labels: np.ndarray, bins: int = 10
) -> dict[str, float]:
    mask = np.isfinite(labels)
    p = probabilities[mask]
    y = (labels[mask] >= 1).astype(float)
    eps = 1e-7
    brier = float(np.mean((p - y) ** 2))
    logloss = float(np.mean(-(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))))
    ece = 0.0
    for low in np.linspace(0, 1, bins, endpoint=False):
        take = (p >= low) & (p < low + 1 / bins)
        if take.any():
            ece += take.mean() * abs(p[take].mean() - y[take].mean())
    return {"brier": brier, "log_loss": logloss, "ece": float(ece)}


def train_gating(
    base: SharedModelEmbeddingRouter,
    data: dict[str, QueryMatrixDataset],
    costs: np.ndarray,
    config: NeuralConfig,
) -> TrainableGatingNetwork:
    for p in base.parameters():
        p.requires_grad_(False)
    gate = TrainableGatingNetwork(config.embedding_dim, len(costs), config.hidden_dim)
    optimizer = torch.optim.AdamW(gate.parameters(), lr=config.learning_rate)
    cost = torch.tensor(costs)[None, :]
    best, state, stale = float("inf"), None, 0
    for _ in range(config.epochs):
        gate.train()
        for batch in _loader(data["train"], config, True):
            with torch.no_grad():
                h = base.encode(batch["tokens"], batch["offsets"])
                q = torch.sigmoid(base(batch["tokens"], batch["offsets"]))
            target = (batch["labels"].nan_to_num(-1) - config.cost_lambda * cost).argmax(1)
            logits = gate(h, q, cost)
            loss = nn.functional.cross_entropy(logits, target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        gate.eval()
        losses = []
        with torch.no_grad():
            for batch in _loader(data["validation"], config, False):
                h = base.encode(batch["tokens"], batch["offsets"])
                q = torch.sigmoid(base(batch["tokens"], batch["offsets"]))
                target = (batch["labels"].nan_to_num(-1) - config.cost_lambda * cost).argmax(1)
                losses.append(float(nn.functional.cross_entropy(gate(h, q, cost), target)))
        val = float(np.mean(losses))
        if val < best - 1e-5:
            best, state, stale = (
                val,
                {k: v.detach().clone() for k, v in gate.state_dict().items()},
                0,
            )
        else:
            stale += 1
        if stale >= config.patience:
            break
    assert state is not None
    gate.load_state_dict(state)
    return gate


def gate_predict(
    base: SharedModelEmbeddingRouter,
    gate: TrainableGatingNetwork,
    dataset: QueryMatrixDataset,
    costs: np.ndarray,
    config: NeuralConfig,
) -> np.ndarray:
    output = []
    cost = torch.tensor(costs)[None, :]
    base.eval()
    gate.eval()
    with torch.no_grad():
        for b in _loader(dataset, config, False):
            output.append(
                gate(
                    base.encode(b["tokens"], b["offsets"]),
                    torch.sigmoid(base(b["tokens"], b["offsets"])),
                    cost,
                ).numpy()
            )
    return np.concatenate(output)


def checkpoint_bytes(model: nn.Module) -> bytes:
    stream = io.BytesIO()
    torch.save(model.state_dict(), stream)
    return stream.getvalue()
