from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def evaluate_preliminary_baselines(
    processed_dir: Path,
    output: Path,
    pool_model_names: list[str],
    *,
    seed: int = 3407,
) -> pd.DataFrame:
    """Evaluate diagnostic baselines without fitting on validation/test labels."""
    models = pd.read_parquet(
        processed_dir / "models.parquet", columns=["model_id", "source_model_id"]
    )
    selected = models[models.source_model_id.isin(pool_model_names)]
    if len(selected) != len(set(pool_model_names)):
        missing = sorted(set(pool_model_names) - set(selected.source_model_id))
        raise ValueError(f"Unknown pool models: {missing}")
    evaluations = pd.read_parquet(
        processed_dir / "evaluations.parquet",
        columns=["query_id", "model_id", "dataset", "quality_score", "historical_cost_usd"],
    )
    splits = pd.read_parquet(processed_dir / "data_splits.parquet", columns=["query_id", "split"])
    evaluations = evaluations[evaluations.model_id.isin(selected.model_id)]

    # Repeated upstream runs are not silently selected. Exclude ambiguous query/model pairs.
    pair_sizes = evaluations.groupby(["query_id", "model_id"]).size()
    unique_pairs = pair_sizes[pair_sizes == 1].index
    evaluations = evaluations.set_index(["query_id", "model_id"]).loc[unique_pairs].reset_index()
    evaluations = evaluations.merge(splits, on="query_id", validate="many_to_one")
    evaluations = evaluations.dropna(subset=["quality_score"])

    rng = np.random.default_rng(seed)
    rows = []
    for dataset, group in evaluations.groupby("dataset"):
        panel = group.pivot(index="query_id", columns="model_id", values="quality_score").dropna()
        if panel.empty:
            continue
        cost_panel = group.pivot(
            index="query_id", columns="model_id", values="historical_cost_usd"
        ).loc[panel.index, panel.columns]
        split_map = splits.set_index("query_id").loc[panel.index, "split"]
        train_ids = split_map[split_map == "train"].index
        test_ids = split_map[split_map == "test"].index
        if not len(train_ids) or not len(test_ids):
            continue
        strongest = panel.loc[train_ids].mean().idxmax()
        cheapest = cost_panel.loc[train_ids].mean().idxmin()
        test_quality = panel.loc[test_ids]
        test_cost = cost_panel.loc[test_ids]
        random_columns = rng.integers(0, len(panel.columns), size=len(test_ids))
        random_quality = test_quality.to_numpy()[np.arange(len(test_ids)), random_columns]
        random_cost = test_cost.to_numpy()[np.arange(len(test_ids)), random_columns]
        oracle_quality = test_quality.max(axis=1)
        oracle_cost = test_cost.where(test_quality.eq(oracle_quality, axis=0)).min(axis=1)
        strategies = {
            "always_strongest_train_selected": (
                test_quality[strongest],
                test_cost[strongest],
                strongest,
            ),
            "always_cheapest_train_selected": (
                test_quality[cheapest],
                test_cost[cheapest],
                cheapest,
            ),
            "random_seeded": (random_quality, random_cost, None),
            "quality_oracle_min_cost_tiebreak": (oracle_quality, oracle_cost, None),
        }
        for strategy, (quality, cost, model_id) in strategies.items():
            rows.append(
                {
                    "dataset": dataset,
                    "strategy": strategy,
                    "pool_size": len(panel.columns),
                    "train_queries": len(train_ids),
                    "test_queries": len(test_ids),
                    "selected_model_id": model_id,
                    "mean_quality": float(np.mean(quality)),
                    "mean_historical_cost_usd": float(np.mean(cost)),
                    "random_seed": seed,
                    "repeated_pairs_policy": "exclude",
                }
            )
    result = pd.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, index=False)
    return result
