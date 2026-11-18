from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

REQUIRED = {
    "models.parquet": {"model_id", "source", "source_model_id", "provenance_source_sha256"},
    "queries.parquet": {"query_id", "dataset", "task_type", "origin_query"},
    "evaluations.parquet": {
        "evaluation_id",
        "query_id",
        "model_id",
        "quality_score",
        "historical_cost_usd",
    },
    "data_splits.parquet": {"query_id", "duplicate_group_id", "split", "random_seed"},
}


def validate_dataset(directory: Path) -> list[str]:
    errors: list[str] = []
    frames: dict[str, pd.DataFrame] = {}
    for filename, columns in REQUIRED.items():
        path = directory / filename
        if not path.exists():
            errors.append(f"missing table: {filename}")
            continue
        available = set(pq.read_schema(path).names)
        missing = columns - available
        if missing:
            errors.append(f"{filename}: missing columns {sorted(missing)}")
            continue
        selected = set(columns)
        if filename == "evaluations.parquet":
            selected.update({"prompt_tokens", "completion_tokens"} & available)
        frames[filename] = pd.read_parquet(path, columns=sorted(selected))
    if errors:
        return errors
    queries, models = frames["queries.parquet"], frames["models.parquet"]
    evaluations, splits = frames["evaluations.parquet"], frames["data_splits.parquet"]
    for name, frame, key in [
        ("models", models, "model_id"),
        ("queries", queries, "query_id"),
        ("evaluations", evaluations, "evaluation_id"),
        ("splits", splits, "query_id"),
    ]:
        if frame[key].isna().any() or frame[key].duplicated().any():
            errors.append(f"{name}: null or duplicate primary key {key}")
    if not set(evaluations.query_id).issubset(set(queries.query_id)):
        errors.append("evaluations: unknown query_id")
    if not set(evaluations.model_id).issubset(set(models.model_id)):
        errors.append("evaluations: unknown model_id")
    if set(splits.query_id) != set(queries.query_id):
        errors.append("splits: query coverage differs from queries")
    leakage = splits.groupby("duplicate_group_id")["split"].nunique()
    if (leakage > 1).any():
        errors.append("splits: duplicate group leakage detected")
    score = evaluations.quality_score.dropna()
    if ((score < 0) | (score > 1)).any():
        errors.append("evaluations: quality_score outside [0, 1]")
    for column in ["historical_cost_usd", "prompt_tokens", "completion_tokens"]:
        if column in evaluations and (evaluations[column].dropna() < 0).any():
            errors.append(f"evaluations: negative {column}")
    return errors
