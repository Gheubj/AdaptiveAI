from __future__ import annotations

import io
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from adaptiveai.neural import NeuralConfig, calibration_metrics, load_neural_data
from adaptiveai.semantic import (
    SemanticMLP,
    SemanticShared,
    budget_violation,
    confidence_fallback,
    deterministic_budget_selection,
    disagreement_fallback,
    fit_semantic_logistic,
    load_embedding_cache,
    logistic_predict,
    predict_torch,
    train_budget_gate,
    train_semantic_torch,
)


def _features(dataset, lookup: dict[str, int], embeddings: np.ndarray) -> np.ndarray:
    return embeddings[[lookup[query_id] for query_id in dataset.ids]]


def _best(labels: np.ndarray) -> int:
    return int(np.nanmean(labels >= 1, axis=0).argmax())


def _metrics(labels: np.ndarray, selection: np.ndarray, costs: np.ndarray) -> dict[str, float]:
    chosen = labels[np.arange(len(labels)), selection]
    success = (chosen >= 1).astype(float)
    return {
        "queries": len(labels),
        "quality": float(success.mean()),
        "mean_score": float(np.nanmean(chosen)),
        "mean_cost": float(costs[selection].mean()),
        "avoidable_failure": float(((chosen < 1) & (np.nanmax(labels, axis=1) >= 1)).mean()),
        "fallback_frequency": float("nan"),
    }


def _rows(dataset, selection: np.ndarray, models: tuple[str, ...], name: str, seed: int):
    chosen = dataset.labels[np.arange(len(dataset)), selection]
    return pd.DataFrame(
        {
            "query_id": dataset.ids,
            "dataset": dataset.datasets,
            "router": name,
            "seed": seed,
            "selected_model_id": [models[index] for index in selection],
            "success": (chosen >= 1).astype(float),
            "score": chosen,
        }
    )


def _fit_hybrid(train, train_x: np.ndarray, seed: int):
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), min_df=2, max_features=30_000, sublinear_tf=True
    )
    lexical = vectorizer.fit_transform(train.texts)
    features = hstack([lexical, csr_matrix(train_x)], format="csr")
    models: list[LogisticRegression | float] = []
    for column in range(train.labels.shape[1]):
        observed = np.isfinite(train.labels[:, column])
        target = (train.labels[observed, column] >= 1).astype(int)
        if np.unique(target).size == 1:
            models.append(float(target[0]))
        else:
            model = LogisticRegression(C=1, max_iter=300, random_state=seed)
            model.fit(features[observed], target)
            models.append(model)
    return vectorizer, models


def _hybrid_predict(vectorizer, models, dataset, semantic: np.ndarray) -> np.ndarray:
    features = hstack([vectorizer.transform(dataset.texts), csr_matrix(semantic)], format="csr")
    return np.column_stack(
        [
            np.full(len(dataset), model)
            if isinstance(model, float)
            else model.predict_proba(features)[:, 1]
            for model in models
        ]
    )


def _select_confidence_threshold(
    probabilities: np.ndarray, labels: np.ndarray, best_model: int
) -> float:
    candidates = np.linspace(0, 0.5, 51)
    scores = []
    for threshold in candidates:
        chosen = confidence_fallback(probabilities, best_model, float(threshold))
        scores.append(float((labels[np.arange(len(labels)), chosen] >= 1).mean()))
    return float(candidates[int(np.argmax(scores))])


def _paired_bootstrap(decisions: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base = baseline.set_index("query_id").success
    rng = np.random.default_rng(3407)
    for (router, seed), frame in decisions.groupby(["router", "seed"]):
        aligned = (
            frame.set_index("query_id").success.to_frame("candidate").join(base.rename("base"))
        )
        delta = (aligned.candidate - aligned.base).to_numpy()
        draws = [rng.choice(delta, len(delta), replace=True).mean() for _ in range(1000)]
        rows.append(
            {
                "router": router,
                "seed": seed,
                "difference": float(delta.mean()),
                "ci_low": float(np.quantile(draws, 0.025)),
                "ci_high": float(np.quantile(draws, 0.975)),
            }
        )
    return pd.DataFrame(rows)


def _cross_dataset(data, train_x: np.ndarray, models: tuple[str, ...], seed: int) -> pd.DataFrame:
    rows = []
    datasets = pd.Series(data["train"].datasets)
    eligible = datasets.value_counts().loc[lambda values: values >= 100].index
    for held_out in eligible:
        evaluate = (datasets == held_out).to_numpy()
        train = ~evaluate
        predictors = fit_semantic_logistic(train_x[train], data["train"].labels[train], seed)
        probabilities = logistic_predict(predictors, train_x[evaluate])
        selection = probabilities.argmax(1)
        labels = data["train"].labels[evaluate]
        best_model = _best(data["train"].labels[train])
        rows.append(
            {
                "held_out_dataset": held_out,
                "queries": int(evaluate.sum()),
                "router_quality": float((labels[np.arange(len(labels)), selection] >= 1).mean()),
                "best_single_quality": float((labels[:, best_model] >= 1).mean()),
                "seed": seed,
                "models": len(models),
            }
        )
    return pd.DataFrame(rows)


def run_pool(
    processed: Path,
    cache: Path,
    output: Path,
    pool: str,
    seeds: tuple[int, ...] = (3407, 3408, 3409, 3410, 3411),
) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    lookup, embeddings = load_embedding_cache(cache)
    data, models, costs, _ = load_neural_data(processed, NeuralConfig(pool=pool))
    x = {split: _features(dataset, lookup, embeddings) for split, dataset in data.items()}
    best_model = _best(data["train"].labels)
    decisions, summaries, calibration, resources = [], [], [], []
    predictions: dict[tuple[str, int, str], np.ndarray] = {}

    started = time.perf_counter()
    logistic = fit_semantic_logistic(x["train"], data["train"].labels, seeds[0])
    training_seconds = time.perf_counter() - started
    for split, dataset in data.items():
        if not len(dataset):
            continue
        probabilities = logistic_predict(logistic, x[split])
        predictions[("semantic_logistic", seeds[0], split)] = probabilities
        selection = probabilities.argmax(1)
        decisions.append(_rows(dataset, selection, models, "semantic_logistic", seeds[0]))
        summaries.append(
            {
                "router": "semantic_logistic",
                "seed": seeds[0],
                "split": split,
                **_metrics(dataset.labels, selection, costs),
            }
        )
        calibration.append(
            {
                "router": "semantic_logistic",
                "seed": seeds[0],
                "split": split,
                **calibration_metrics(probabilities, dataset.labels),
            }
        )
    resources.append(
        {
            "router": "semantic_logistic",
            "seed": seeds[0],
            "training_seconds": training_seconds,
            "parameters": int(
                sum(
                    model.coef_.size + model.intercept_.size
                    for model in logistic
                    if not isinstance(model, float)
                )
            ),
        }
    )

    started = time.perf_counter()
    vectorizer, hybrid = _fit_hybrid(data["train"], x["train"], seeds[0])
    hybrid_seconds = time.perf_counter() - started
    for split in ("validation", "test", "ood_test"):
        if not len(data[split]):
            continue
        probabilities = _hybrid_predict(vectorizer, hybrid, data[split], x[split])
        selection = probabilities.argmax(1)
        decisions.append(_rows(data[split], selection, models, "hybrid", seeds[0]))
        summaries.append(
            {
                "router": "hybrid",
                "seed": seeds[0],
                "split": split,
                **_metrics(data[split].labels, selection, costs),
            }
        )
    resources.append(
        {
            "router": "hybrid",
            "seed": seeds[0],
            "training_seconds": hybrid_seconds,
            "parameters": int(len(vectorizer.vocabulary_) * len(models)),
        }
    )

    for seed in seeds:
        for name, model in (
            ("semantic_mlp", SemanticMLP(x["train"].shape[1], len(models))),
            ("semantic_shared", SemanticShared(x["train"].shape[1], len(models))),
        ):
            info = train_semantic_torch(
                model,
                x["train"],
                data["train"].labels,
                x["validation"],
                data["validation"].labels,
                seed,
            )
            buffer = io.BytesIO()
            torch.save(model.state_dict(), buffer)
            resources.append(
                {
                    "router": name,
                    "seed": seed,
                    "training_seconds": info["seconds"],
                    "parameters": sum(p.numel() for p in model.parameters()),
                    "checkpoint_bytes": len(buffer.getvalue()),
                    "epochs": info["epochs"],
                }
            )
            torch.save(model.state_dict(), output / f"{name}-seed{seed}.pt")
            for split in ("validation", "test", "ood_test"):
                if not len(data[split]):
                    continue
                probabilities = predict_torch(model, x[split])
                predictions[(name, seed, split)] = probabilities
                selection = probabilities.argmax(1)
                decisions.append(_rows(data[split], selection, models, name, seed))
                summaries.append(
                    {
                        "router": name,
                        "seed": seed,
                        "split": split,
                        **_metrics(data[split].labels, selection, costs),
                    }
                )
                calibration.append(
                    {
                        "router": name,
                        "seed": seed,
                        "split": split,
                        **calibration_metrics(probabilities, data[split].labels),
                    }
                )

    threshold = _select_confidence_threshold(
        predictions[("semantic_mlp", seeds[0], "validation")],
        data["validation"].labels,
        best_model,
    )
    for split in ("validation", "test", "ood_test"):
        if not len(data[split]):
            continue
        first = predictions[("semantic_mlp", seeds[0], split)]
        second = predictions[("semantic_shared", seeds[0], split)]
        for name, selection in (
            ("confidence_fallback", confidence_fallback(first, best_model, threshold)),
            ("disagreement_fallback", disagreement_fallback(first, second, best_model)),
            ("best_single", np.full(len(data[split]), best_model)),
            ("oracle", np.nanargmax(data[split].labels, axis=1)),
        ):
            rows = _rows(data[split], selection, models, name, seeds[0])
            decisions.append(rows)
            summary = {
                "router": name,
                "seed": seeds[0],
                "split": split,
                **_metrics(data[split].labels, selection, costs),
            }
            if "fallback" in name:
                original = first.argmax(1)
                summary["fallback_frequency"] = float((selection != original).mean())
            summaries.append(summary)

    if pool == "proprietary8":
        quality = predictions[("semantic_logistic", seeds[0], "train")]
        validation_quality = logistic_predict(logistic, x["validation"])
        test_quality = logistic_predict(logistic, x["test"])
        best_cost = float(costs[best_model])
        gating_rows = []
        for fraction in (0.25, 0.5, 0.75, 1.0):
            budget = best_cost * fraction
            val_selection, penalty = deterministic_budget_selection(
                validation_quality, costs, budget
            )
            deterministic = (test_quality - penalty * costs[None, :]).argmax(1)
            gate, history = train_budget_gate(
                x["train"], quality, data["train"].labels, costs, budget, seeds[0]
            )
            with torch.no_grad():
                gate_selection = (
                    gate(
                        torch.tensor(x["test"]),
                        torch.tensor(test_quality),
                        torch.tensor(costs)[None, :],
                    )
                    .argmax(1)
                    .numpy()
                )
            for name, selection in (
                ("validation_budget_selector", deterministic),
                ("revised_trainable_gate", gate_selection),
            ):
                metrics = _metrics(data["test"].labels, selection, costs)
                gating_rows.append(
                    {
                        "router": name,
                        "budget_fraction": fraction,
                        "budget": budget,
                        "validation_penalty": penalty,
                        "validation_cost": float(costs[val_selection].mean()),
                        "constraint_violation": budget_violation(selection, costs, budget),
                        "final_dual": history["dual"][-1],
                        **metrics,
                    }
                )
        pd.DataFrame(gating_rows).to_parquet(output / "matched_budget_gating.parquet", index=False)
        _cross_dataset(data, x["train"], models, seeds[0]).to_parquet(
            output / "cross_dataset.parquet", index=False
        )

    decision_frame = pd.concat(decisions, ignore_index=True)
    decision_frame["split"] = decision_frame.query_id.map(
        {query_id: split for split, dataset in data.items() for query_id in dataset.ids}
    )
    decision_frame.to_parquet(output / "decisions.parquet", index=False)
    pd.DataFrame(summaries).to_parquet(output / "summary.parquet", index=False)
    pd.DataFrame(calibration).to_parquet(output / "calibration.parquet", index=False)
    pd.DataFrame(resources).to_parquet(output / "resources.parquet", index=False)
    test = decision_frame[decision_frame.split == "test"]
    baseline = test[(test.router == "best_single") & (test.seed == seeds[0])]
    _paired_bootstrap(test[test.router != "best_single"], baseline).to_parquet(
        output / "paired_bootstrap.parquet", index=False
    )
    decision_frame.groupby(["router", "seed", "split", "dataset"], as_index=False).agg(
        quality=("success", "mean"), queries=("query_id", "size")
    ).to_parquet(output / "per_dataset.parquet", index=False)
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "pool": pool,
                "seeds": seeds,
                "encoder": "all-MiniLM-L6-v2",
                "protocol": "train/validation development; repeated test and ARC exploratory",
                "confidence_threshold": threshold,
                "models": models,
            },
            indent=2,
        )
    )
    return output
