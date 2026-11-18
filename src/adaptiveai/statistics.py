from __future__ import annotations

import numpy as np
import pandas as pd


def bootstrap_mean_ci(
    frame: pd.DataFrame,
    value: str,
    *,
    group: str = "duplicate_group_id",
    strata: str | None = "dataset",
    seed: int = 3407,
    samples: int = 2000,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Cluster bootstrap: duplicate groups, optionally stratified by dataset."""
    if frame.empty:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    strata_groups = [(None, frame)] if strata is None else list(frame.groupby(strata, sort=True))
    prepared: list[tuple[np.ndarray, np.ndarray]] = []
    for _, part in strata_groups:
        clusters = part.groupby(group, sort=False)[value].agg(["sum", "count"])
        prepared.append((clusters["sum"].to_numpy(), clusters["count"].to_numpy()))
    estimates = np.empty(samples)
    for index in range(samples):
        total, count = 0.0, 0
        for sums, counts in prepared:
            chosen = rng.integers(0, len(sums), size=len(sums))
            total += float(sums[chosen].sum())
            count += int(counts[chosen].sum())
        estimates[index] = total / count
    alpha = (1 - confidence) / 2
    return tuple(float(x) for x in np.quantile(estimates, [alpha, 1 - alpha]))


def paired_bootstrap_difference(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    value: str = "quality_score",
    seed: int = 3407,
    samples: int = 2000,
) -> tuple[float, float, float]:
    joined = left[["query_id", value]].merge(
        right[["query_id", value]],
        on="query_id",
        suffixes=("_left", "_right"),
        validate="one_to_one",
    )
    differences = joined[f"{value}_left"] - joined[f"{value}_right"]
    rng = np.random.default_rng(seed)
    means = np.array(
        [
            rng.choice(differences.to_numpy(), len(differences), replace=True).mean()
            for _ in range(samples)
        ]
    )
    return (
        float(differences.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )
