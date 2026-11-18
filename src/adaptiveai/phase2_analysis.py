from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from adaptiveai.protocol import (
    LIGHTWEIGHT20,
    PAPER_COST_DATASETS,
    PAPER_PERFORMANCE_DATASETS,
    PAPER_PROPRIETARY13,
    SOURCE_SHA256,
)
from adaptiveai.resolution import classify_repeats


def analyze_reconciliation(processed: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    evaluations = pd.read_parquet(
        processed / "evaluations.parquet",
        columns=[
            "evaluation_id",
            "query_id",
            "model_id",
            "dataset",
            "source_split",
            "quality_score",
            "provenance_source_file",
            "provenance_record_index",
        ],
    )
    models = pd.read_parquet(processed / "models.parquet", columns=["model_id", "source_model_id"])
    repeats = classify_repeats(evaluations)
    repeats.to_parquet(output / "repeat_classification.parquet", index=False)
    model_lookup = models.set_index("source_model_id").model_id
    paper_models = set(model_lookup.loc[list(LIGHTWEIGHT20)]) | set(
        model_lookup.loc[list(PAPER_PROPRIETARY13)]
    )
    paper_datasets = set(PAPER_PERFORMANCE_DATASETS) | set(PAPER_COST_DATASETS)
    paper = evaluations[
        evaluations.model_id.isin(paper_models) & evaluations.dataset.isin(paper_datasets)
    ]
    summary = {
        "source_sha256": SOURCE_SHA256,
        "extended": {
            "records": len(evaluations),
            "datasets": evaluations.dataset.nunique(),
            "models": evaluations.model_id.nunique(),
        },
        "paper_manifest_filter_approximation": {
            "records_before_repeat_resolution": len(paper),
            "datasets": paper.dataset.nunique(),
            "models": paper.model_id.nunique(),
        },
        "repeated_pairs": len(repeats),
        "repeat_classes": repeats.classification.value_counts().to_dict(),
        "missing_scores": int(evaluations.quality_score.isna().sum()),
        "note": (
            "The exact 391,645 paper instances cannot be reconstructed from names alone; "
            "the paper uses 20+13 models, whereas the two settings overlap in datasets and "
            "archive releases."
        ),
    }
    (output / "reconciliation_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def make_phase2_plots(run_dir: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    summary = pd.read_parquet(run_dir / "summary.parquet")
    per_dataset = pd.read_parquet(run_dir / "per_dataset.parquet")
    summary.to_csv(output / "quality_cost.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    points = summary.dropna(subset=["mean_cost"])
    ax.scatter(points.mean_cost, points.quality)
    for row in points.itertuples():
        ax.annotate(row.router, (row.mean_cost, row.quality), fontsize=7)
    ax.set(
        xlabel="Mean historical monetary cost (USD/query)",
        ylabel="Task success rate",
        title="Quality–cost trade-off (test; post-hoc Oracle marked)",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "quality_vs_cost.png", dpi=220)
    plt.close(fig)
    best = float(summary.loc[summary.router == "best_single", "mean_cost"].iloc[0])
    summary["cost_savings_vs_best"] = 1 - summary.mean_cost / best if best else float("nan")
    summary["quality_retention_vs_best"] = summary.quality / float(
        summary.loc[summary.router == "best_single", "quality"].iloc[0]
    )
    summary.to_csv(output / "savings_retention.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.scatter(summary["cost_savings_vs_best"], summary["quality_retention_vs_best"])
    for row in summary.itertuples():
        ax.annotate(
            row.router,
            (row.cost_savings_vs_best, row.quality_retention_vs_best),
            fontsize=7,
        )
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.set(
        xlabel="Cost savings relative to Best Single",
        ylabel="Quality retention relative to Best Single",
        title="Cost savings versus quality retention",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "cost_savings_vs_quality_retention.png", dpi=220)
    plt.close(fig)
    comparison = summary[~summary.router.str.startswith("random_seed_")].copy()
    comparison = comparison.sort_values("quality")
    comparison.to_csv(output / "router_comparison.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    axes[0].barh(comparison.router, comparison.gain_vs_best_single)
    axes[0].axvline(0, color="black", linewidth=0.8)
    axes[0].set(xlabel="Success difference", title="Router vs Best Single")
    axes[1].barh(comparison.router, comparison.gap_to_oracle)
    axes[1].set(xlabel="Success difference", title="Gap to post-hoc Oracle")
    fig.tight_layout()
    fig.savefig(output / "router_vs_best_and_oracle.png", dpi=220)
    plt.close(fig)
    chosen = per_dataset[
        per_dataset.router.isin(["best_single", "tfidf_logistic", "oracle_upper_bound"])
    ]
    pivot = chosen.pivot(index="dataset", columns="router", values="quality").sort_index()
    pivot.to_csv(output / "performance_by_task.csv")
    ax = pivot.plot(kind="bar", figsize=(10, 5))
    ax.set(ylabel="Task success rate", title="Performance by benchmark")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output / "performance_by_task.png", dpi=220)
    plt.close()
