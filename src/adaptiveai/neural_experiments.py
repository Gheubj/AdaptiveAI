from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from adaptiveai.neural import (
    NeuralConfig,
    SharedModelEmbeddingRouter,
    SparseNeuralRouter,
    calibration_metrics,
    checkpoint_bytes,
    fit_temperature,
    gate_predict,
    load_neural_data,
    predict,
    train_gating,
    train_predictor,
)
from adaptiveai.protocol import SOURCE_SHA256
from adaptiveai.statistics import bootstrap_mean_ci


def _routing_rows(
    name: str,
    dataset,
    selections: np.ndarray,
    models: tuple[str, ...],
    costs: np.ndarray,
    split_lookup: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    labels = dataset.labels
    chosen = labels[np.arange(len(labels)), selections]
    oracle = np.nanmax(labels, axis=1)
    return pd.DataFrame(
        {
            "query_id": dataset.ids,
            "duplicate_group_id": [split_lookup.loc[i, "duplicate_group_id"] for i in dataset.ids],
            "dataset": dataset.datasets,
            "router": name,
            "seed": seed,
            "selected_model_id": [models[i] for i in selections],
            "success": (chosen >= 1).astype(float),
            "quality_score": chosen,
            "historical_cost_usd": costs[selections],
            "avoidable_failure": ((chosen < 1) & (oracle >= 1)),
        }
    )


def _summary(frame: pd.DataFrame) -> dict:
    lo, hi = bootstrap_mean_ci(frame, "success", seed=int(frame.seed.iloc[0]), samples=1000)
    return {
        "router": frame.router.iloc[0],
        "seed": int(frame.seed.iloc[0]),
        "split": "unknown",
        "queries": len(frame),
        "quality": float(frame.success.mean()),
        "quality_ci_low": lo,
        "quality_ci_high": hi,
        "mean_cost": float(frame.historical_cost_usd.mean()),
        "avoidable_failure_rate": float(frame.avoidable_failure.mean()),
    }


def run_neural_suite(
    processed: Path,
    output: Path,
    *,
    pool: str = "proprietary8",
    seeds: tuple[int, ...] = (3407, 3408, 3409, 3410, 3411),
) -> Path:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    all_decisions = []
    summaries = []
    calibration = []
    resources = []
    for seed in seeds:
        config = NeuralConfig(pool=pool, seed=seed)
        data, models, costs, split_lookup = load_neural_data(processed, config)
        architectures = {
            "architecture_a_sparse": SparseNeuralRouter(
                config.buckets, len(models), config.embedding_dim, config.hidden_dim, config.dropout
            ),
            "architecture_b_shared": SharedModelEmbeddingRouter(
                config.buckets, len(models), config.embedding_dim, config.hidden_dim, config.dropout
            ),
        }
        trained = {}
        for name, model in architectures.items():
            info = train_predictor(model, data, config)
            trained[name] = model
            val_logits, val_labels, _ = predict(model, data["validation"], config)
            temperature = fit_temperature(val_logits, val_labels)
            for split in ("validation", "test", "ood_test"):
                if not len(data[split]):
                    continue
                logits, labels, elapsed = predict(model, data[split], config)
                raw = 1 / (1 + np.exp(-logits))
                calibrated = 1 / (1 + np.exp(-logits / temperature))
                for variant, prob in ((name, raw), (name + "_calibrated", calibrated)):
                    selections = prob.argmax(1)
                    rows = _routing_rows(
                        variant, data[split], selections, models, costs, split_lookup, seed
                    )
                    rows["split"] = split
                    all_decisions.append(rows)
                    row = _summary(rows)
                    row["split"] = split
                    summaries.append(row)
                calibration.extend(
                    [
                        {
                            "router": name,
                            "seed": seed,
                            "split": split,
                            "variant": "raw",
                            **calibration_metrics(raw, labels),
                        },
                        {
                            "router": name,
                            "seed": seed,
                            "split": split,
                            "variant": "temperature",
                            "temperature": temperature,
                            **calibration_metrics(calibrated, labels),
                        },
                    ]
                )
                resources.append(
                    {
                        "router": name,
                        "seed": seed,
                        "split": split,
                        "training_seconds": info["training_seconds"],
                        "epochs": len(info["history"]),
                        "model_bytes": len(checkpoint_bytes(model)),
                        "inference_seconds": elapsed,
                        "milliseconds_per_query": 1000 * elapsed / len(data[split]),
                    }
                )
        base = trained["architecture_b_shared"]
        normalized_cost = costs / max(float(costs.max()), 1e-8)
        gate = train_gating(base, data, normalized_cost, config)
        val_logits, val_labels, _ = predict(base, data["validation"], config)
        temperature = fit_temperature(val_logits, val_labels)
        for split in ("validation", "test", "ood_test"):
            if not len(data[split]):
                continue
            logits, _, _ = predict(base, data[split], config)
            probabilities = 1 / (1 + np.exp(-logits / temperature))
            deterministic = (probabilities - config.cost_lambda * normalized_cost[None, :]).argmax(
                1
            )
            gate_selection = gate_predict(base, gate, data[split], normalized_cost, config).argmax(
                1
            )
            for name, selection in (
                ("deterministic_constrained_selector", deterministic),
                ("architecture_c_trainable_gate", gate_selection),
            ):
                rows = _routing_rows(
                    name, data[split], selection, models, costs, split_lookup, seed
                )
                rows["split"] = split
                all_decisions.append(rows)
                row = _summary(rows)
                row["split"] = split
                summaries.append(row)
        for name, model in {**architectures, "architecture_c_trainable_gate": gate}.items():
            target = output / f"{name}-seed{seed}.pt"
            target.write_bytes(checkpoint_bytes(model))
    decisions = pd.concat(all_decisions, ignore_index=True)
    summary = pd.DataFrame(summaries)
    cal = pd.DataFrame(calibration)
    resource = pd.DataFrame(resources)
    decisions.to_parquet(output / "decisions.parquet", index=False)
    summary.to_parquet(output / "summary_by_seed.parquet", index=False)
    cal.to_parquet(output / "calibration.parquet", index=False)
    resource.to_parquet(output / "resources.parquet", index=False)
    decisions.groupby(["router", "seed", "split", "dataset"], as_index=False).agg(
        quality=("success", "mean"),
        mean_cost=("historical_cost_usd", "mean"),
        queries=("query_id", "size"),
    ).to_parquet(output / "per_dataset.parquet", index=False)
    manifest = {
        "source_sha256": SOURCE_SHA256,
        "pool": pool,
        "seeds": seeds,
        "config": asdict(NeuralConfig(pool=pool)),
        "torch": torch.__version__,
        "device": "cpu",
        "runtime_completed_utc": pd.Timestamp.utcnow().isoformat(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return output


def run_ablation(processed: Path, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for dim in (16, 64):
        for objective in ("bce", "mse"):
            config = NeuralConfig(pool="proprietary8", seed=3407, embedding_dim=dim)
            data, models, costs, lookup = load_neural_data(processed, config)
            for arch in ("sparse", "shared"):
                model = (SparseNeuralRouter if arch == "sparse" else SharedModelEmbeddingRouter)(
                    config.buckets, len(models), dim, config.hidden_dim, config.dropout
                )
                info = train_predictor(model, data, config, objective=objective)
                logits, _, _ = predict(model, data["validation"], config)
                selection = logits.argmax(1)
                routed = _routing_rows(
                    f"{arch}_{objective}_d{dim}",
                    data["validation"],
                    selection,
                    models,
                    costs,
                    lookup,
                    3407,
                )
                rows.append(
                    {
                        "architecture": arch,
                        "objective": objective,
                        "embedding_dim": dim,
                        "validation_quality": routed.success.mean(),
                        "training_seconds": info["training_seconds"],
                        "epochs": len(info["history"]),
                    }
                )
    result = pd.DataFrame(rows)
    result.to_parquet(output / "ablation_results.parquet", index=False)
    return output
