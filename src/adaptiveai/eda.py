from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/adaptiveai-matplotlib")
import matplotlib.pyplot as plt
import pandas as pd


def run_eda(processed_dir: Path, report_dir: Path) -> dict:
    queries = pd.read_parquet(processed_dir / "queries.parquet")
    evaluations = pd.read_parquet(
        processed_dir / "evaluations.parquet",
        columns=[
            "evaluation_id",
            "query_id",
            "model_id",
            "dataset",
            "quality_score",
            "historical_cost_usd",
            "prompt_tokens",
            "completion_tokens",
        ],
    )
    models = pd.read_parquet(processed_dir / "models.parquet")
    report_dir.mkdir(parents=True, exist_ok=True)
    coverage = evaluations.groupby("query_id")["model_id"].nunique()
    duplicate_eval_count = int(evaluations.duplicated(["query_id", "model_id"]).sum())
    summary = {
        "unique_queries": int(queries.query_id.nunique()),
        "unique_models": int(models.model_id.nunique()),
        "datasets": queries.dataset.value_counts(dropna=False).to_dict(),
        "evaluations": len(evaluations),
        "duplicate_query_model_pairs": duplicate_eval_count,
        "missing": {
            "quality_score": int(evaluations.quality_score.isna().sum()),
            "historical_cost_usd": int(evaluations.historical_cost_usd.isna().sum()),
            "prompt_tokens": int(evaluations.prompt_tokens.isna().sum()),
            "completion_tokens": int(evaluations.completion_tokens.isna().sum()),
        },
        "models_per_query": {
            "min": int(coverage.min()) if len(coverage) else 0,
            "median": float(coverage.median()) if len(coverage) else 0,
            "max": int(coverage.max()) if len(coverage) else 0,
        },
        "fully_comparable_queries": int((coverage == models.model_id.nunique()).sum()),
        "quality_by_dataset": evaluations.groupby("dataset")["quality_score"]
        .agg(["count", "mean", "std"])
        .fillna(0)
        .to_dict("index"),
        "interpretation_warning": (
            "Dataset metrics may use different evaluators and are not assumed "
            "comparable across tasks. "
            "Comparisons must use matched query/model coverage and metric semantics."
        ),
    }
    (report_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    axes = (
        queries.dataset.value_counts()
        .sort_values()
        .plot.barh(figsize=(8, 5), title="Queries by dataset")
    )
    axes.set_xlabel("Unique queries")
    axes.figure.tight_layout()
    axes.figure.savefig(report_dir / "queries_by_dataset.png", dpi=160)
    plt.close(axes.figure)

    axes = coverage.plot.hist(
        bins=max(1, min(30, int(coverage.nunique()))),
        figsize=(7, 4),
        title="Model coverage per query",
    )
    axes.set_xlabel("Models with an evaluation")
    axes.figure.tight_layout()
    axes.figure.savefig(report_dir / "coverage_per_query.png", dpi=160)
    plt.close(axes.figure)

    quality = evaluations.quality_score.dropna()
    if len(quality):
        axes = quality.plot.hist(bins=20, figsize=(7, 4), title="Upstream quality scores")
        axes.set_xlabel("Score (upstream metric)")
        axes.figure.tight_layout()
        axes.figure.savefig(report_dir / "quality_distribution.png", dpi=160)
        plt.close(axes.figure)

    costs = evaluations.historical_cost_usd.dropna()
    costs = costs[costs >= 0]
    if len(costs):
        axes = costs.plot.hist(bins=40, figsize=(7, 4), title="Historical request costs")
        axes.set_xlabel("USD (upstream observation)")
        axes.set_yscale("log")
        axes.figure.tight_layout()
        axes.figure.savefig(report_dir / "cost_distribution.png", dpi=160)
        plt.close(axes.figure)

    performance = (
        evaluations.groupby(["dataset", "model_id"])["quality_score"]
        .agg(["count", "mean", "std"])
        .reset_index()
    )
    performance["sem"] = performance["std"] / performance["count"].pow(0.5)
    performance["ci95_low_normal"] = performance["mean"] - 1.96 * performance["sem"]
    performance["ci95_high_normal"] = performance["mean"] + 1.96 * performance["sem"]
    performance.to_parquet(report_dir / "model_performance_by_benchmark.parquet", index=False)

    cost_quality = (
        evaluations.groupby(["dataset", "model_id"])
        .agg(
            matched_observations=("query_id", "nunique"),
            mean_quality=("quality_score", "mean"),
            mean_historical_cost_usd=("historical_cost_usd", "mean"),
        )
        .reset_index()
    )
    cost_quality.to_parquet(report_dir / "quality_cost_by_benchmark.parquet", index=False)
    plot_data = cost_quality.dropna(subset=["mean_quality", "mean_historical_cost_usd"])
    if len(plot_data):
        figure, axes = plt.subplots(figsize=(8, 5))
        for dataset, group in plot_data.groupby("dataset"):
            axes.scatter(
                group.mean_historical_cost_usd,
                group.mean_quality,
                alpha=0.65,
                label=dataset,
            )
        axes.set_xlabel("Mean historical cost (USD; matched within benchmark only)")
        axes.set_ylabel("Mean upstream score")
        if plot_data.dataset.nunique() <= 12:
            axes.legend(fontsize=7)
        figure.tight_layout()
        figure.savefig(report_dir / "quality_cost_tradeoff.png", dpi=160)
        plt.close(figure)

    coverage_table = pd.crosstab(evaluations.dataset, evaluations.model_id)
    figure, axes = plt.subplots(
        figsize=(max(8, 0.28 * len(coverage_table.columns)), max(4, 0.3 * len(coverage_table)))
    )
    image = axes.imshow(coverage_table.to_numpy(), aspect="auto", interpolation="nearest")
    axes.set_yticks(range(len(coverage_table.index)), coverage_table.index, fontsize=7)
    axes.set_xlabel("Model index (see coverage_heatmap_models.json)")
    axes.set_title("Evaluation count by benchmark and model")
    figure.colorbar(image, ax=axes, label="Evaluations")
    figure.tight_layout()
    figure.savefig(report_dir / "coverage_heatmap.png", dpi=160)
    plt.close(figure)
    (report_dir / "coverage_heatmap_models.json").write_text(
        json.dumps(dict(enumerate(coverage_table.columns)), indent=2), encoding="utf-8"
    )

    pairwise_rows = []
    for dataset, group in evaluations.dropna(subset=["quality_score"]).groupby("dataset"):
        pivot = group.pivot_table(index="query_id", columns="model_id", values="quality_score")
        columns = list(pivot.columns)
        for left_index, left in enumerate(columns):
            for right in columns[left_index + 1 :]:
                matched = pivot[[left, right]].dropna()
                if matched.empty:
                    continue
                difference = matched[left] - matched[right]
                pairwise_rows.append(
                    {
                        "dataset": dataset,
                        "model_left": left,
                        "model_right": right,
                        "matched_queries": len(matched),
                        "left_wins": int((difference > 0).sum()),
                        "ties": int((difference == 0).sum()),
                        "right_wins": int((difference < 0).sum()),
                        "mean_score_difference": float(difference.mean()),
                    }
                )
    pd.DataFrame(pairwise_rows).to_parquet(
        report_dir / "pairwise_model_comparisons.parquet", index=False
    )
    return summary
