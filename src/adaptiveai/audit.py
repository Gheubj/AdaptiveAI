from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from adaptiveai.io import iter_json_documents
from adaptiveai.normalize import infer_path_metadata


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def audit_archive(archive: Path, output: Path) -> dict[str, Any]:
    datasets: Counter[str] = Counter()
    models: Counter[str] = Counter()
    splits: Counter[str] = Counter()
    top_fields: defaultdict[str, Counter[str]] = defaultdict(Counter)
    record_fields: defaultdict[str, Counter[str]] = defaultdict(Counter)
    missing: Counter[str] = Counter()
    file_count = record_count = invalid_paths = non_list_records = 0
    dataset_fields: defaultdict[str, set[str]] = defaultdict(set)

    for member, document in iter_json_documents(archive):
        file_count += 1
        try:
            dataset, path_split, model = infer_path_metadata(member)
        except ValueError:
            invalid_paths += 1
            continue
        split = str(document.get("split") or path_split)
        datasets[dataset] += 1
        splits[split] += 1
        models[model] += 1
        for key, value in document.items():
            top_fields[key][_type_name(value)] += 1
            dataset_fields[dataset].add(key)
        records = document.get("records")
        if not isinstance(records, list):
            non_list_records += 1
            continue
        record_count += len(records)
        for record in records:
            if not isinstance(record, dict):
                record_fields["<record>"][_type_name(record)] += 1
                continue
            for key in (
                "origin_query",
                "prompt",
                "prediction",
                "ground_truth",
                "score",
                "raw_output",
                "prompt_tokens",
                "completion_tokens",
                "cost",
            ):
                if key not in record or record[key] is None:
                    missing[key] += 1
            for key, value in record.items():
                record_fields[key][_type_name(value)] += 1

    result = {
        "archive": str(archive),
        "files": file_count,
        "records": record_count,
        "datasets": dict(sorted(datasets.items())),
        "models": dict(sorted(models.items())),
        "splits": dict(sorted(splits.items())),
        "invalid_paths": invalid_paths,
        "files_with_non_list_records": non_list_records,
        "top_level_field_types": {key: dict(value) for key, value in sorted(top_fields.items())},
        "record_field_types": {key: dict(value) for key, value in sorted(record_fields.items())},
        "record_missing_counts": dict(missing),
        "dataset_top_level_fields": {
            key: sorted(value) for key, value in sorted(dataset_fields.items())
        },
        "semantic_cautions": [
            "time_taken is retained as benchmark-file aggregate time, not request latency",
            "score semantics depend on the dataset evaluator and are not globally interchangeable",
            "missing numeric values are preserved as null and are never imputed as zero",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def coverage_analysis(processed_dir: Path, output_dir: Path) -> dict[str, Any]:
    evaluations = pd.read_parquet(
        processed_dir / "evaluations.parquet",
        columns=["query_id", "model_id", "dataset", "quality_score", "historical_cost_usd"],
    )
    models = pd.read_parquet(processed_dir / "models.parquet")
    output_dir.mkdir(parents=True, exist_ok=True)
    pairs = evaluations[["query_id", "model_id", "dataset"]].drop_duplicates()
    per_query = pairs.groupby(["dataset", "query_id"])["model_id"].nunique().rename("model_count")
    per_query.reset_index().to_parquet(output_dir / "coverage_per_query.parquet", index=False)
    intersection = pd.crosstab(pairs["query_id"], pairs["model_id"]).astype("uint32")
    pairwise = intersection.T.dot(intersection)
    pairwise.to_parquet(output_dir / "model_pair_intersection.parquet")
    model_coverage = pairs.groupby(["dataset", "model_id"])["query_id"].nunique().rename("queries")
    model_coverage.reset_index().to_parquet(output_dir / "model_coverage.parquet", index=False)
    by_dataset = per_query.groupby("dataset").agg(
        queries="size",
        median_models="median",
        min_models="min",
        max_models="max",
    )
    for threshold in (2, 3, 5):
        by_dataset[f"queries_ge_{threshold}_models"] = per_query.groupby("dataset").apply(
            lambda values, limit=threshold: int((values >= limit).sum()),
            include_groups=False,
        )
    by_dataset.reset_index().to_parquet(output_dir / "coverage_by_dataset.parquet", index=False)
    name_map = models.set_index("model_id")["source_model_id"].to_dict()
    summary = {
        "unique_queries": int(pairs.query_id.nunique()),
        "unique_models": int(pairs.model_id.nunique()),
        "unique_datasets": int(pairs.dataset.nunique()),
        "queries_ge_2_models": int((per_query >= 2).sum()),
        "queries_ge_3_models": int((per_query >= 3).sum()),
        "queries_ge_5_models": int((per_query >= 5).sum()),
        "answers_per_query": {
            "min": int(per_query.min()),
            "median": float(per_query.median()),
            "max": int(per_query.max()),
        },
        "model_names": name_map,
        "artifacts": [
            "coverage_per_query.parquet",
            "model_pair_intersection.parquet",
            "model_coverage.parquet",
            "coverage_by_dataset.parquet",
        ],
    }
    (output_dir / "coverage_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary
