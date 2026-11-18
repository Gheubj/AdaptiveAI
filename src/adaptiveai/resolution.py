from __future__ import annotations

import pandas as pd


def resolve_evaluations(frame: pd.DataFrame, policy: str = "mean") -> pd.DataFrame:
    """Resolve repeated query/model observations without imputing missing scores."""
    keys = ["query_id", "model_id"]
    ordered = frame.sort_values(keys + ["provenance_source_file", "provenance_record_index"])
    if policy == "exclude":
        sizes = ordered.groupby(keys).size()
        keep = sizes[sizes == 1].index
        return ordered.set_index(keys).loc[keep].reset_index()
    if policy == "representative":
        return ordered.drop_duplicates(keys, keep="first").reset_index(drop=True)
    if policy != "mean":
        raise ValueError(f"Unknown resolution policy: {policy}")
    numeric = ["quality_score", "historical_cost_usd", "prompt_tokens", "completion_tokens"]
    available = [column for column in numeric if column in ordered]
    first = [column for column in ordered.columns if column not in keys + available]
    aggregation = {
        **{column: "mean" for column in available},
        **{column: "first" for column in first},
    }
    result = ordered.groupby(keys, as_index=False, sort=True).agg(aggregation)
    counts = ordered.groupby(keys, sort=True).size().rename("repeat_count").reset_index()
    return result.merge(counts, on=keys, validate="one_to_one")


def classify_repeats(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(["query_id", "model_id"], dropna=False)
    aggregations = {
        "records": ("evaluation_id", "size"),
        "observed_scores": ("quality_score", "count"),
        "distinct_scores": ("quality_score", "nunique"),
        "source_files": ("provenance_source_file", "nunique"),
    }
    if "raw_output_json" in frame:
        aggregations["distinct_outputs"] = ("raw_output_json", "nunique")
    result = grouped.agg(**aggregations).reset_index()
    result = result[result.records > 1].copy()
    result["classification"] = "repeated_release_same_score_output_uninspected"
    if "distinct_outputs" in result:
        result["classification"] = "identical_duplicate"
        result.loc[result.distinct_outputs > 1, "classification"] = "repeated_generation_same_score"
    result.loc[result.distinct_scores > 1, "classification"] = "conflicting_evaluation"
    result.loc[result.observed_scores < result.records, "classification"] = "contains_missing_score"
    return result
