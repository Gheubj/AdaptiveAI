from __future__ import annotations

import io
import json
import os
import time
from pathlib import Path

import joblib
import numpy as np
import psutil
import torch

from adaptiveai.neural import NeuralConfig, SparseNeuralRouter, hash_tokens, load_neural_data
from adaptiveai.routers import TfidfSuccessRouter
from adaptiveai.semantic import (
    ENCODER_ID,
    ENCODER_REVISION,
    BudgetGate,
    SemanticMLP,
    fit_semantic_logistic,
    load_embedding_cache,
    logistic_predict,
    train_budget_gate,
)


def _timed(callable_, repeats: int) -> tuple[float, float]:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        callable_()
        samples.append(1000 * (time.perf_counter() - started))
    return float(np.median(samples)), float(np.quantile(samples, 0.95))


def run_compute_benchmark(processed: Path, output: Path) -> Path:
    from sentence_transformers import SentenceTransformer

    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    data, models, costs, _ = load_neural_data(processed, NeuralConfig(pool="proprietary8"))
    train, test = data["train"], data["test"]
    process = psutil.Process(os.getpid())
    rows = []

    outcomes = {model: train.labels[:, index] for index, model in enumerate(models)}
    started = time.perf_counter()
    tfidf = TfidfSuccessRouter(seed=3407).fit(train.texts, outcomes)
    checkpoint = output / "tfidf_frozen.joblib"
    joblib.dump(tfidf, checkpoint)
    del tfidf
    rss_before = process.memory_info().rss
    load_started = time.perf_counter()
    tfidf = joblib.load(checkpoint)
    load_seconds = time.perf_counter() - load_started
    rss_after = process.memory_info().rss
    tfidf.vectorizer.transform(test.texts[:128])

    def single():
        return tfidf.predict_utilities(test.texts[0], models)

    def batch():
        return tfidf.vectorizer.transform(test.texts[:128])

    p50, p95 = _timed(single, 50)
    batch_p50, _ = _timed(batch, 10)
    rows.append(
        _row(
            "tfidf",
            p50,
            p95,
            batch_p50,
            load_seconds,
            rss_after - rss_before,
            checkpoint.stat().st_size,
            128,
            training_seconds=time.perf_counter() - started,
            process_rss_bytes=rss_after,
        )
    )

    sparse = SparseNeuralRouter(20_000, len(models), 32, 64, 0.1)
    rss_before = process.memory_info().rss
    load_started = time.perf_counter()
    sparse.load_state_dict(
        torch.load(
            "reports/phase3/proprietary8-main/architecture_a_sparse-seed3407.pt",
            weights_only=True,
        )
    )
    sparse.eval()
    load_seconds = time.perf_counter() - load_started
    rss_after = process.memory_info().rss

    def sparse_call(texts: list[str]):
        token_rows = [hash_tokens(text, 20_000) for text in texts]
        offsets = torch.tensor(np.cumsum([0] + [len(row) for row in token_rows[:-1]]))
        tokens = torch.tensor([token for row in token_rows for token in row])
        with torch.no_grad():
            sparse(tokens, offsets)

    sparse_call(test.texts[:128])
    p50, p95 = _timed(lambda: sparse_call(test.texts[:1]), 50)
    batch_p50, _ = _timed(lambda: sparse_call(test.texts[:128]), 10)
    sparse_checkpoint = Path("reports/phase3/proprietary8-main/architecture_a_sparse-seed3407.pt")
    rows.append(
        _row(
            "sparse_a",
            p50,
            p95,
            batch_p50,
            load_seconds,
            rss_after - rss_before,
            sparse_checkpoint.stat().st_size,
            128,
            process_rss_bytes=rss_after,
        )
    )

    rss_before = process.memory_info().rss
    load_started = time.perf_counter()
    encoder = SentenceTransformer(ENCODER_ID, revision=ENCODER_REVISION)
    encoder.max_seq_length = 128
    semantic = SemanticMLP(384, len(models))
    semantic.load_state_dict(
        torch.load("reports/phase3_5/proprietary8/semantic_mlp-seed3407.pt", weights_only=True)
    )
    semantic.eval()
    load_seconds = time.perf_counter() - load_started
    encoder_load_seconds = load_seconds
    encoder_rss_delta = rss_after - rss_before
    rss_after = process.memory_info().rss

    def semantic_call(texts: list[str]):
        embedding = encoder.encode(
            texts, batch_size=len(texts), normalize_embeddings=True, show_progress_bar=False
        )
        with torch.no_grad():
            semantic(torch.tensor(embedding))

    semantic_call(test.texts[:8])
    p50, p95 = _timed(lambda: semantic_call(test.texts[:1]), 30)
    batch_p50, _ = _timed(lambda: semantic_call(test.texts[:128]), 5)
    semantic_checkpoint = Path("reports/phase3_5/proprietary8/semantic_mlp-seed3407.pt")
    rows.append(
        _row(
            "semantic_mlp",
            p50,
            p95,
            batch_p50,
            load_seconds,
            rss_after - rss_before,
            semantic_checkpoint.stat().st_size,
            128,
            cache_bytes=(processed / "minilm_embeddings.npz").stat().st_size,
            process_rss_bytes=rss_after,
        )
    )

    cache_lookup, embedding_cache = load_embedding_cache(processed / "minilm_embeddings.npz")
    x_train = embedding_cache[[cache_lookup[query_id] for query_id in train.ids]]
    quality_model = fit_semantic_logistic(x_train, train.labels, 3407)
    quality_train = logistic_predict(quality_model, x_train)
    best_model = int(np.nanmean(train.labels >= 1, axis=0).argmax())
    gate, _ = train_budget_gate(
        x_train, quality_train, train.labels, costs, float(costs[best_model]), 3407
    )
    gate_checkpoint = output / "revised_gate_full_budget.pt"
    buffer = io.BytesIO()
    torch.save(gate.state_dict(), buffer)
    gate_checkpoint.write_bytes(buffer.getvalue())
    rss_before = process.memory_info().rss
    load_started = time.perf_counter()
    loaded_gate = BudgetGate(384, len(models))
    loaded_gate.load_state_dict(torch.load(gate_checkpoint, weights_only=True))
    loaded_gate.eval()
    load_seconds = time.perf_counter() - load_started
    rss_after = process.memory_info().rss

    def gate_call(texts: list[str]):
        embedding = encoder.encode(
            texts, batch_size=len(texts), normalize_embeddings=True, show_progress_bar=False
        )
        quality = logistic_predict(quality_model, embedding)
        with torch.no_grad():
            loaded_gate(
                torch.tensor(embedding), torch.tensor(quality), torch.tensor(costs)[None, :]
            )

    gate_call(test.texts[:8])
    p50, p95 = _timed(lambda: gate_call(test.texts[:1]), 30)
    batch_p50, _ = _timed(lambda: gate_call(test.texts[:128]), 5)
    rows.append(
        _row(
            "revised_gate",
            p50,
            p95,
            batch_p50,
            encoder_load_seconds + load_seconds,
            encoder_rss_delta + rss_after - rss_before,
            gate_checkpoint.stat().st_size,
            128,
            cache_bytes=(processed / "minilm_embeddings.npz").stat().st_size,
            process_rss_bytes=rss_after,
        )
    )
    (output / "compute_benchmark.json").write_text(json.dumps(rows, indent=2))
    return output


def _row(name, p50, p95, batch_ms, loading, rss, checkpoint, batch_size, **extra):
    return {
        "router": name,
        "single_p50_ms": p50,
        "single_p95_ms": p95,
        "batch_128_ms": batch_ms,
        "batch_throughput_qps": batch_size / (batch_ms / 1000),
        "loading_seconds": loading,
        "rss_load_delta_bytes": max(0, rss),
        "checkpoint_bytes": checkpoint,
        **extra,
    }
