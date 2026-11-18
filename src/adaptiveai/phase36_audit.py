from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from adaptiveai.neural import NeuralConfig, load_neural_data
from adaptiveai.semantic import (
    deterministic_budget_selection,
    fit_semantic_logistic,
    load_embedding_cache,
    logistic_predict,
    train_budget_gate,
)


def _bootstrap_difference(
    first: pd.DataFrame, second: pd.DataFrame, *, samples: int = 10_000
) -> tuple[float, float, float]:
    merged = first[["query_id", "success"]].merge(
        second[["query_id", "success"]], on="query_id", suffixes=("_a", "_b")
    )
    delta = (merged.success_a - merged.success_b).to_numpy()
    rng = np.random.default_rng(3407)
    draws = np.empty(samples)
    for index in range(samples):
        draws[index] = rng.choice(delta, len(delta), replace=True).mean()
    return float(delta.mean()), float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _standardize(frame: pd.DataFrame, router: str, fraction: float, budget: float) -> pd.DataFrame:
    result = frame.copy()
    result["router"] = router
    result["budget_fraction"] = fraction
    result["budget"] = budget
    return result[
        [
            "query_id",
            "duplicate_group_id",
            "router",
            "budget_fraction",
            "budget",
            "selected_model_id",
            "success",
            "historical_cost_usd",
        ]
    ]


def run_matched_budget_audit(processed: Path, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    data, models, costs, lookup = load_neural_data(processed, NeuralConfig(pool="proprietary8"))
    cache_lookup, embeddings = load_embedding_cache(processed / "minilm_embeddings.npz")
    features = {
        split: embeddings[[cache_lookup[query_id] for query_id in dataset.ids]]
        for split, dataset in data.items()
    }
    quality_model = fit_semantic_logistic(features["train"], data["train"].labels, 3407)
    quality = {split: logistic_predict(quality_model, value) for split, value in features.items()}
    best_model = int(np.nanmean(data["train"].labels >= 1, axis=0).argmax())
    best_cost = float(costs[best_model])
    phase2_validation = pd.read_parquet(
        "reports/phase2/runs/proprietary8-validation-8db20881e516/decisions.parquet"
    )
    phase2_test = pd.read_parquet(
        "reports/phase2/runs/proprietary8-test-c0bdfbfd3c59/decisions.parquet"
    )
    phase3 = pd.read_parquet("reports/phase3/proprietary8-main/decisions.parquet")
    phase3 = phase3[(phase3.split == "test") & (phase3.seed == 3407)]
    decisions = []
    histories = []
    for fraction in (0.25, 0.5, 0.75, 1.0):
        budget = best_cost * fraction
        validation_selection, penalty = deterministic_budget_selection(
            quality["validation"], costs, budget
        )
        test_selection = (quality["test"] - penalty * costs[None, :]).argmax(1)
        base = pd.DataFrame(
            {
                "query_id": data["test"].ids,
                "duplicate_group_id": [
                    lookup.loc[q, "duplicate_group_id"] for q in data["test"].ids
                ],
                "selected_model_id": [models[index] for index in test_selection],
                "success": (
                    data["test"].labels[np.arange(len(test_selection)), test_selection] >= 1
                ).astype(float),
                "historical_cost_usd": costs[test_selection],
            }
        )
        decisions.append(_standardize(base, "deterministic_budget_selector", fraction, budget))

        gate, history = train_budget_gate(
            features["train"], quality["train"], data["train"].labels, costs, budget, 3407
        )
        with torch.no_grad():
            gate_selection = (
                gate(
                    torch.tensor(features["test"]),
                    torch.tensor(quality["test"]),
                    torch.tensor(costs)[None, :],
                )
                .argmax(1)
                .numpy()
            )
        gate_frame = base.copy()
        gate_frame["selected_model_id"] = [models[index] for index in gate_selection]
        gate_frame["success"] = (
            data["test"].labels[np.arange(len(gate_selection)), gate_selection] >= 1
        ).astype(float)
        gate_frame["historical_cost_usd"] = costs[gate_selection]
        decisions.append(_standardize(gate_frame, "revised_trainable_gate", fraction, budget))
        histories.append(
            {
                "budget_fraction": fraction,
                "penalty": penalty,
                "history": history,
                "validation_cost": float(costs[validation_selection].mean()),
            }
        )

        for name, historical_name in (
            ("best_single", "best_single"),
            ("cheapest", "cheapest"),
        ):
            frame = phase2_test[phase2_test.router == historical_name]
            decisions.append(_standardize(frame, name, fraction, budget))
        for name, historical_name in (
            ("original_trainable_gate", "architecture_c_trainable_gate"),
            ("original_deterministic_selector", "deterministic_constrained_selector"),
        ):
            frame = phase3[phase3.router == historical_name]
            decisions.append(_standardize(frame, name, fraction, budget))

        candidates = phase2_validation[phase2_validation.router.str.startswith("cost_constrained")]
        candidate_cost = candidates.groupby("router").historical_cost_usd.mean()
        feasible = candidate_cost[candidate_cost <= budget * 1.005]
        chosen = feasible.idxmax() if len(feasible) else "cheapest"
        test_name = chosen if chosen != "cheapest" else "cheapest"
        frame = phase2_test[phase2_test.router == test_name]
        decisions.append(_standardize(frame, "validation_cost_constrained_tfidf", fraction, budget))

    all_decisions = pd.concat(decisions, ignore_index=True)
    all_decisions.to_parquet(output / "matched_budget_decisions.parquet", index=False)
    summary = all_decisions.groupby(["router", "budget_fraction", "budget"], as_index=False).agg(
        queries=("query_id", "size"),
        quality=("success", "mean"),
        mean_cost=("historical_cost_usd", "mean"),
    )
    summary["quality_per_dollar"] = summary.quality / summary.mean_cost.clip(lower=1e-12)
    summary["mean_constraint_violation"] = (summary.mean_cost - summary.budget).clip(lower=0)
    summary["violates_budget"] = summary.mean_constraint_violation > 0
    intervals = []
    for fraction in (0.25, 0.5, 0.75, 1.0):
        subset = all_decisions[all_decisions.budget_fraction == fraction]
        reference = subset[subset.router == "deterministic_budget_selector"]
        for router, frame in subset.groupby("router"):
            difference, low, high = _bootstrap_difference(frame, reference)
            intervals.append(
                {
                    "router": router,
                    "budget_fraction": fraction,
                    "difference_vs_deterministic": difference,
                    "ci_low": low,
                    "ci_high": high,
                }
            )
    summary = summary.merge(pd.DataFrame(intervals), on=["router", "budget_fraction"])
    summary.to_parquet(output / "matched_budget_summary.parquet", index=False)
    selections = all_decisions.groupby(
        ["router", "budget_fraction", "selected_model_id"], as_index=False
    ).size()
    selections["share"] = selections["size"] / selections.groupby(["router", "budget_fraction"])[
        "size"
    ].transform("sum")
    selections.to_parquet(output / "selection_distribution.parquet", index=False)
    (output / "training_histories.json").write_text(json.dumps(histories, indent=2))

    figure, axis = plt.subplots(figsize=(8, 5))
    for router, frame in summary.groupby("router"):
        axis.plot(frame.mean_cost, frame.quality, marker="o", label=router)
    axis.set(xlabel="Mean historical cost (USD)", ylabel="Success", title="Matched-budget audit")
    axis.grid(alpha=0.25)
    axis.legend(fontsize=7, ncol=2)
    figure.tight_layout()
    figure.savefig(output / "pareto_frontier.png", dpi=180)
    plt.close(figure)
    return output
