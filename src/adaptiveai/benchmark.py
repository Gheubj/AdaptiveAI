from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from adaptiveai.protocol import DEFAULT_SEED, LIGHTWEIGHT20, PROPRIETARY8, TASK_BY_DATASET
from adaptiveai.resolution import resolve_evaluations
from adaptiveai.routers import (
    CheapestRouter,
    FixedRouter,
    RandomRouter,
    RoutingDecision,
    RoutingRequest,
    TaskAwareRouter,
    TfidfSuccessRouter,
    oracle_decision,
)
from adaptiveai.statistics import bootstrap_mean_ci


@dataclass(frozen=True)
class BenchmarkConfig:
    pool: str = "lightweight20"
    split: str = "test"
    resolution_policy: str = "mean"
    seed: int = DEFAULT_SEED
    random_repeats: int = 5
    bootstrap_samples: int = 1000
    tfidf_c: float = 1.0
    max_features: int = 30_000
    cost_penalties: tuple[float, ...] = (0.0, 1.0, 5.0, 20.0, 100.0)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _load_panel(
    processed: Path, pool_names: tuple[str, ...], policy: str
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    models = pd.read_parquet(processed / "models.parquet", columns=["model_id", "source_model_id"])
    selected = models[models.source_model_id.isin(pool_names)]
    if len(selected) != len(pool_names):
        raise ValueError(f"Pool mismatch: expected {len(pool_names)}, found {len(selected)}")
    model_ids = tuple(sorted(selected.model_id))
    columns = [
        "evaluation_id",
        "query_id",
        "model_id",
        "dataset",
        "quality_score",
        "historical_cost_usd",
        "prompt_tokens",
        "completion_tokens",
        "provenance_source_file",
        "provenance_record_index",
    ]
    evaluations = pd.read_parquet(processed / "evaluations.parquet", columns=columns)
    evaluations = evaluations[evaluations.model_id.isin(model_ids)]
    return resolve_evaluations(evaluations, policy), model_ids


def _complete_queries(frame: pd.DataFrame, models: tuple[str, ...]) -> set[str]:
    usable = frame.dropna(subset=["quality_score"])
    counts = usable.groupby("query_id").model_id.nunique()
    return set(counts[counts == len(models)].index)


def select_best_single(quality: pd.DataFrame) -> str:
    """Select on the supplied fitting matrix only, with deterministic tie-breaking."""
    means = quality.mean().sort_index()
    best = means.max()
    return str(means[means == best].index[0])


def _train_routers(
    panel: pd.DataFrame,
    queries: pd.DataFrame,
    split_map: pd.DataFrame,
    models: tuple[str, ...],
    config: BenchmarkConfig,
    *,
    cost_aware: bool = False,
) -> tuple[dict[str, Any], dict[str, float]]:
    train_ids = set(split_map.loc[split_map.split == "train", "query_id"])
    train = panel[panel.query_id.isin(train_ids)]
    complete = _complete_queries(train, models)
    train = train[train.query_id.isin(complete)]
    quality = train.pivot(index="query_id", columns="model_id", values="quality_score").reindex(
        columns=models
    )
    cost = train.pivot(index="query_id", columns="model_id", values="historical_cost_usd").reindex(
        columns=models
    )
    expected_costs = cost.mean().dropna().to_dict()
    best = select_best_single(quality)
    merged_queries = queries.set_index("query_id").loc[quality.index]
    texts = merged_queries.origin_query.fillna(merged_queries.prompt).fillna("").tolist()
    outcomes = {model: quality[model].to_numpy() for model in models}
    tfidf = TfidfSuccessRouter(max_features=config.max_features, c=config.tfidf_c, seed=config.seed)
    tfidf.fit(texts, outcomes, expected_costs=expected_costs)
    task_models = {}
    train_meta = train.assign(task=train.dataset.map(TASK_BY_DATASET).fillna("other"))
    for task, group in train_meta.groupby("task"):
        task_models[task] = group.groupby("model_id").quality_score.mean().idxmax()
    routers: dict[str, Any] = {
        "best_single": FixedRouter(best),
        "task_aware_metadata": TaskAwareRouter(task_models, best),
        "tfidf_logistic": tfidf,
    }
    if cost_aware and len(expected_costs) == len(models):
        routers["cheapest"] = CheapestRouter(expected_costs)
    return routers, expected_costs


def _evaluate_router(
    name: str,
    router: Any,
    test: pd.DataFrame,
    queries: pd.DataFrame,
    models: tuple[str, ...],
    splits: pd.DataFrame,
) -> pd.DataFrame:
    query_lookup = queries.set_index("query_id")
    split_lookup = splits.set_index("query_id")
    groups = list(test.groupby("query_id", sort=True))
    batch_selected: dict[str, str] = {}
    if isinstance(router, TfidfSuccessRouter):
        query_ids = [str(query_id) for query_id, _ in groups]
        texts = []
        for query_id in query_ids:
            query = query_lookup.loc[query_id]
            text = query.origin_query
            if pd.isna(text):
                text = query.prompt
            texts.append("" if pd.isna(text) else str(text))
        matrix = router.vectorizer.transform(texts)
        utilities = np.empty((len(query_ids), len(models)))
        for column, model in enumerate(models):
            predictor = router.models[model]
            probability = (
                np.full(len(query_ids), predictor)
                if isinstance(predictor, float)
                else predictor.predict_proba(matrix)[:, 1]
            )
            utilities[:, column] = probability - router.cost_penalty * router.expected_costs.get(
                model, 0.0
            )
        selected_columns = np.argmax(utilities, axis=1)
        batch_selected = {
            query_id: models[column]
            for query_id, column in zip(query_ids, selected_columns, strict=True)
        }
    rows = []
    for query_id, group in groups:
        query = query_lookup.loc[query_id]
        outcomes = group.set_index("model_id").quality_score.to_dict()
        costs = group.set_index("model_id").historical_cost_usd.to_dict()
        text = query.origin_query
        if pd.isna(text):
            text = query.prompt
        request = RoutingRequest(
            str(query_id),
            "" if pd.isna(text) else str(text),
            models,
            {"task_type": TASK_BY_DATASET.get(str(query.dataset), "other")},
        )
        if name == "oracle_upper_bound":
            decision = oracle_decision(outcomes, costs)
        elif batch_selected:
            decision = RoutingDecision(batch_selected[str(query_id)])
        else:
            decision = router.route(request)
        selected = group[group.model_id == decision.model_id].iloc[0]
        rows.append(
            {
                "query_id": query_id,
                "duplicate_group_id": split_lookup.loc[query_id, "duplicate_group_id"],
                "dataset": selected.dataset,
                "router": name,
                "selected_model_id": decision.model_id,
                "quality_score": float(selected.quality_score),
                "success": float(selected.quality_score >= 1.0),
                "historical_cost_usd": selected.historical_cost_usd,
                "successful_alternative": bool((group.quality_score >= 1.0).any()),
                "avoidable_failure": bool(
                    selected.quality_score < 1.0 and (group.quality_score >= 1.0).any()
                ),
            }
        )
    return pd.DataFrame(rows)


def run_benchmark(processed: Path, output_root: Path, config: BenchmarkConfig) -> Path:
    started = time.perf_counter()
    pool_names = LIGHTWEIGHT20 if config.pool == "lightweight20" else PROPRIETARY8
    panel, models = _load_panel(processed, pool_names, config.resolution_policy)
    queries = pd.read_parquet(
        processed / "queries.parquet", columns=["query_id", "dataset", "origin_query", "prompt"]
    )
    splits = pd.read_parquet(processed / "data_splits.parquet")
    complete = _complete_queries(panel, models)
    target_ids = set(splits.loc[splits.split == config.split, "query_id"]) & complete
    test = panel[panel.query_id.isin(target_ids)].dropna(subset=["quality_score"])
    if test.empty:
        available = panel[
            panel.query_id.isin(set(splits.loc[splits.split == config.split, "query_id"]))
        ].model_id.nunique()
        raise ValueError(
            f"No complete {len(models)}-model panel for split={config.split}; "
            f"the split contains only {available} pool models with any observation"
        )
    routers, expected_costs = _train_routers(
        panel, queries, splits, models, config, cost_aware=config.pool == "proprietary8"
    )
    decisions = []
    for name, router in routers.items():
        decisions.append(_evaluate_router(name, router, test, queries, models, splits))
    for repeat in range(config.random_repeats):
        decisions.append(
            _evaluate_router(
                f"random_seed_{config.seed + repeat}",
                RandomRouter(config.seed + repeat),
                test,
                queries,
                models,
                splits,
            )
        )
    decisions.append(_evaluate_router("oracle_upper_bound", None, test, queries, models, splits))
    if config.pool == "proprietary8":
        tfidf = routers["tfidf_logistic"]
        for penalty in config.cost_penalties:
            tfidf.set_cost_penalty(penalty)
            decisions.append(
                _evaluate_router(
                    f"cost_constrained_lambda_{penalty:g}", tfidf, test, queries, models, splits
                )
            )
    detail = pd.concat(decisions, ignore_index=True)
    rows = []
    for router, frame in detail.groupby("router"):
        low, high = bootstrap_mean_ci(
            frame, "success", seed=config.seed, samples=config.bootstrap_samples
        )
        probabilities = frame.selected_model_id.value_counts(normalize=True)
        rows.append(
            {
                "router": router,
                "queries": len(frame),
                "quality": frame.success.mean(),
                "quality_ci_low": low,
                "quality_ci_high": high,
                "mean_score": frame.quality_score.mean(),
                "mean_cost": frame.historical_cost_usd.mean(),
                "total_cost": frame.historical_cost_usd.sum(),
                "cost_per_success": frame.historical_cost_usd.sum() / max(frame.success.sum(), 1),
                "selection_entropy": float(-(probabilities * np.log(probabilities)).sum()),
                "avoidable_failure_rate": frame.avoidable_failure.mean(),
            }
        )
    summary = pd.DataFrame(rows)
    best_quality = float(summary.loc[summary.router == "best_single", "quality"].iloc[0])
    oracle_quality = float(summary.loc[summary.router == "oracle_upper_bound", "quality"].iloc[0])
    summary["gain_vs_best_single"] = summary.quality - best_quality
    summary["gap_to_oracle"] = oracle_quality - summary.quality
    manifest = {
        "config": asdict(config),
        "config_hash": stable_hash(asdict(config)),
        "pool_models": pool_names,
        "split_manifest_hash": stable_hash(splits.to_dict("records")),
        "expected_costs_train": expected_costs,
        "runtime_seconds": time.perf_counter() - started,
        "pid": os.getpid(),
    }
    run_id = f"{config.pool}-{config.split}-{manifest['config_hash'][:12]}"
    output = output_root / run_id
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite experiment: {output}")
    output.mkdir(parents=True)
    detail.to_parquet(output / "decisions.parquet", index=False)
    summary.to_parquet(output / "summary.parquet", index=False)
    detail.groupby(["router", "dataset"], as_index=False).agg(
        queries=("query_id", "size"),
        quality=("success", "mean"),
        mean_score=("quality_score", "mean"),
        mean_cost=("historical_cost_usd", "mean"),
        avoidable_failure_rate=("avoidable_failure", "mean"),
    ).to_parquet(output / "per_dataset.parquet", index=False)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return output
