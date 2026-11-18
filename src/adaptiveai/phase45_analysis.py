from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from adaptiveai.phase45_benchmark import SEED, bootstrap_mean
from adaptiveai.routers import TfidfSuccessRouter
from adaptiveai.semantic import fit_semantic_logistic, logistic_predict


def _matrix(outputs: pd.DataFrame, split: str) -> tuple[list[str], np.ndarray]:
    frame = outputs[outputs.split == split].pivot(
        index="query_id", columns="model_id", values="correct"
    )
    return list(frame.columns), frame.to_numpy(float)


def _bootstrap_accuracy(values: np.ndarray, seed: int = SEED) -> tuple[float, float]:
    return bootstrap_mean(values.astype(float), seed=seed)


def _paired_interval(
    first: np.ndarray, second: np.ndarray, seed: int = SEED
) -> tuple[float, float]:
    return bootstrap_mean((first - second).astype(float), seed=seed)


def analyze_phase45(
    panel_path: Path,
    outputs_path: Path,
    phase4_profile_path: Path,
    output_dir: Path,
    semantic_embeddings: np.ndarray | None = None,
) -> dict[str, object]:
    panel = pd.read_parquet(panel_path).set_index("query_id")
    outputs = pd.read_parquet(outputs_path)
    profile = pd.read_parquet(phase4_profile_path)
    models, train_y = _matrix(outputs, "train")
    _, validation_y = _matrix(outputs, "validation")
    _, test_y = _matrix(outputs, "test")
    train_ids = sorted(outputs.loc[outputs.split == "train", "query_id"].unique())
    validation_ids = sorted(outputs.loc[outputs.split == "validation", "query_id"].unique())
    test_ids = sorted(outputs.loc[outputs.split == "test", "query_id"].unique())

    warm = profile[profile.state == "warm"]
    p95 = warm.groupby("model_id").latency_seconds.quantile(0.95).to_dict()
    memory = profile.groupby("model_id").rss_bytes.max().to_dict()
    fastest = min(models, key=p95.get)
    strongest = models[int(validation_y.mean(axis=0).argmax())]

    tfidf_candidates = []
    for c in (0.1, 1.0, 10.0):
        router = TfidfSuccessRouter(c=c, seed=SEED).fit(
            panel.loc[train_ids].prompt.tolist(),
            {model: train_y[:, index] for index, model in enumerate(models)},
        )
        selected = [
            max(models, key=router.predict_utilities(text, tuple(models)).get)
            for text in panel.loc[validation_ids].prompt
        ]
        score = np.mean([validation_y[i, models.index(model)] for i, model in enumerate(selected)])
        tfidf_candidates.append((score, -c, router))
    tfidf = max(tfidf_candidates, key=lambda item: (item[0], item[1]))[2]

    semantic_predictions = None
    semantic_validation_accuracy = None
    if semantic_embeddings is not None:
        semantic_models = fit_semantic_logistic(semantic_embeddings[:150], train_y, SEED)
        semantic_predictions = logistic_predict(semantic_models, semantic_embeddings[250:])
        semantic_validation = logistic_predict(semantic_models, semantic_embeddings[150:250])
        semantic_validation_accuracy = float(
            validation_y[np.arange(len(validation_y)), semantic_validation.argmax(1)].mean()
        )

    task_model = {}
    validation_tasks = panel.loc[validation_ids].task.to_numpy()
    for task in sorted(set(validation_tasks)):
        mask = validation_tasks == task
        task_model[task] = models[int(validation_y[mask].mean(axis=0).argmax())]

    rng = np.random.default_rng(SEED)
    rows = []
    indexed = outputs[outputs.split == "test"].set_index(["query_id", "model_id"])
    for query_index, query_id in enumerate(test_ids):
        prompt, task = panel.loc[query_id, ["prompt", "task"]]
        tfidf_model = max(models, key=tfidf.predict_utilities(prompt, tuple(models)).get)
        choices = {
            "fixed_fastest": fastest,
            "fixed_strongest": strongest,
            "random": models[int(rng.integers(len(models)))],
            "task_aware": task_model[task],
            "tfidf": tfidf_model,
            "latency_aware": fastest,
            "memory_aware": min(models, key=memory.get),
            "hardware_aware": strongest,
        }
        if semantic_predictions is not None:
            choices["semantic"] = models[int(semantic_predictions[query_index].argmax())]
        oracle_index = int(
            np.lexsort((np.array([p95[m] for m in models]), -test_y[query_index]))[0]
        )
        choices["oracle"] = models[oracle_index]
        for policy, model in choices.items():
            observed = indexed.loc[(query_id, model)]
            rows.append(
                {
                    "query_id": query_id,
                    "task": task,
                    "policy": policy,
                    "selected_model_id": model,
                    "correct": observed.correct,
                    "latency_seconds": observed.latency_seconds,
                    "ttft_seconds": observed.ttft_seconds,
                    "rss_bytes": memory[model],
                    "failure": observed.failure_status is not None,
                    "predicted_p95_latency": p95[model],
                    "latency_budget": max(p95.values()),
                    "constraint_violation": bool(
                        pd.notna(observed.latency_seconds)
                        and observed.latency_seconds > max(p95.values())
                    ),
                }
            )
    decisions = pd.DataFrame(rows)
    decisions.to_parquet(output_dir / "policy_decisions.parquet", index=False)

    summaries = []
    for policy, group in decisions.groupby("policy"):
        low, high = _bootstrap_accuracy(group.correct.to_numpy())
        summaries.append(
            {
                "policy": policy,
                "quality": group.correct.mean(),
                "quality_ci_low": low,
                "quality_ci_high": high,
                "p50_latency": group.latency_seconds.median(),
                "p95_latency": group.latency_seconds.quantile(0.95),
                "peak_ram_bytes": group.rss_bytes.max(),
                "failure_rate": group.failure.mean(),
                "constraint_violations": int(group.constraint_violation.sum()),
                "smol_selection_rate": float(group.selected_model_id.eq(strongest).mean()),
            }
        )
    policy_summary = pd.DataFrame(summaries).sort_values("policy")
    policy_summary.to_parquet(output_dir / "policy_summary.parquet", index=False)

    model_rows = []
    test_outputs = outputs[outputs.split == "test"]
    for model, group in test_outputs.groupby("model_id"):
        low, high = _bootstrap_accuracy(group.correct.to_numpy())
        model_rows.append(
            {
                "model_id": model,
                "quality": group.correct.mean(),
                "quality_ci_low": low,
                "quality_ci_high": high,
                "p50_latency": group.latency_seconds.median(),
                "p95_latency": group.latency_seconds.quantile(0.95),
                "peak_ram_bytes": memory[model],
                "failures": int(group.failure_status.notna().sum()),
            }
        )
    model_summary = pd.DataFrame(model_rows)
    model_summary.to_parquet(output_dir / "model_summary.parquet", index=False)

    a, b = test_y[:, 0].astype(bool), test_y[:, 1].astype(bool)
    both = int((a & b).sum())
    only_a, only_b = int((a & ~b).sum()), int((~a & b).sum())
    neither = int((~a & ~b).sum())
    oracle = np.maximum(a, b).astype(float)
    best = test_y[:, int(validation_y.mean(axis=0).argmax())]
    fastest_values = test_y[:, models.index(fastest)]
    oracle_low, oracle_high = _bootstrap_accuracy(oracle)
    complementarity = {
        "model_a": models[0],
        "model_b": models[1],
        "both_correct": both,
        "only_a_correct": only_a,
        "only_b_correct": only_b,
        "both_incorrect": neither,
        "disagreement_rate": (only_a + only_b) / len(a),
        "correctness_phi": float(np.corrcoef(a.astype(float), b.astype(float))[0, 1]),
        "oracle_accuracy": float(oracle.mean()),
        "oracle_ci": [oracle_low, oracle_high],
        "oracle_gain_best_single": float(oracle.mean() - best.mean()),
        "oracle_gain_fastest": float(oracle.mean() - fastest_values.mean()),
    }

    fastest_group = decisions[decisions.policy == "fixed_fastest"].sort_values("query_id")
    comparisons = []
    for policy, group in decisions.groupby("policy"):
        group = group.sort_values("query_id")
        delta = group.correct.to_numpy() - fastest_group.correct.to_numpy()
        low, high = _paired_interval(group.correct.to_numpy(), fastest_group.correct.to_numpy())
        positive, negative = int((delta > 0).sum()), int((delta < 0).sum())
        pvalue = (
            float(binomtest(min(positive, negative), positive + negative, 0.5).pvalue)
            if positive + negative
            else 1.0
        )
        comparisons.append(
            {
                "policy": policy,
                "accuracy_difference_vs_fastest": delta.mean(),
                "difference_ci_low": low,
                "difference_ci_high": high,
                "mcnemar_discordant_positive": positive,
                "mcnemar_discordant_negative": negative,
                "mcnemar_exact_p": pvalue,
                "median_latency_difference": float(
                    np.nanmedian(
                        group.latency_seconds.to_numpy() - fastest_group.latency_seconds.to_numpy()
                    )
                ),
            }
        )
    comparison_frame = pd.DataFrame(comparisons)
    comparison_frame.to_parquet(output_dir / "paired_comparisons.parquet", index=False)
    metadata: dict[str, object] = {
        "fastest": fastest,
        "strongest_validation": strongest,
        "task_models": task_model,
        "tfidf_validation_accuracy": max(item[0] for item in tfidf_candidates),
        "semantic_validation_accuracy": semantic_validation_accuracy,
        "complementarity": complementarity,
    }
    (output_dir / "analysis_metadata.json").write_text(json.dumps(metadata, indent=2))
    return metadata
