from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import ValidationError

from adaptiveai.io import iter_json_documents, sha256_file
from adaptiveai.schemas import BenchmarkRecord

PATH_RE = re.compile(
    r"(?:^|/)bench/(?P<dataset>[^/]+)/(?P<split>[^/]+)/(?P<model>[^/]+)/[^/]+\.json$"
)
RELEASE_PATH_RE = re.compile(
    r"(?:^|/)bench-release/(?P<dataset>[^/]+)/"
    r"(?:(?P<split>[^/]+)/)?(?P<model>[^/]+)/[^/]+\.json$"
)

EVALUATION_SCHEMA = pa.schema(
    [
        ("evaluation_id", pa.string()),
        ("query_id", pa.string()),
        ("model_id", pa.string()),
        ("dataset", pa.string()),
        ("source_split", pa.string()),
        ("evaluation_method", pa.string()),
        ("metric_name", pa.string()),
        ("quality_score", pa.float64()),
        ("prediction_json", pa.string()),
        ("raw_output_json", pa.string()),
        ("prompt_tokens", pa.int64()),
        ("completion_tokens", pa.int64()),
        ("historical_cost_usd", pa.float64()),
        ("aggregate_file_time_seconds", pa.float64()),
        ("request_latency_seconds", pa.float64()),
        ("source_extra_json", pa.string()),
        ("provenance_source_sha256", pa.string()),
        ("provenance_source_file", pa.string()),
        ("provenance_record_index", pa.int64()),
    ]
)


def stable_id(*parts: object) -> str:
    material = "\x1f".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def canonical_text(value: str) -> str:
    return " ".join(value.casefold().split())


def infer_path_metadata(name: str) -> tuple[str, str, str]:
    normalized = name.replace("\\", "/")
    match = PATH_RE.search(normalized)
    if match:
        return match.group("dataset"), match.group("split"), match.group("model")
    release_match = RELEASE_PATH_RE.search(normalized)
    if release_match:
        return (
            release_match.group("dataset"),
            release_match.group("split") or "unspecified",
            release_match.group("model"),
        )
    raise ValueError(f"Unrecognized LLMRouterBench result path: {name}")


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _write_batch(writer: pq.ParquetWriter | None, path: Path, rows: list[dict]) -> pq.ParquetWriter:
    table = pa.Table.from_pylist(rows, schema=EVALUATION_SCHEMA)
    if writer is None:
        writer = pq.ParquetWriter(path, EVALUATION_SCHEMA, compression="zstd")
    writer.write_table(table)
    rows.clear()
    return writer


def normalize_archive(
    archive: Path, output_dir: Path, *, evaluation_batch_size: int = 5_000
) -> dict[str, int]:
    source_sha = sha256_file(archive)
    queries: dict[str, dict[str, Any]] = {}
    models: dict[str, dict[str, Any]] = {}
    evaluations: list[dict[str, Any]] = []
    evaluation_count = 0
    errors: list[dict[str, str]] = []
    seen_evaluations: set[str] = set()

    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_path = output_dir / "evaluations.parquet"
    temporary_evaluations = output_dir / "evaluations.parquet.inprogress"
    writer: pq.ParquetWriter | None = None
    try:
        for member, document in iter_json_documents(archive):
            try:
                dataset, path_split, model_name = infer_path_metadata(member)
            except ValueError as exc:
                errors.append({"source_file": member, "record_index": "", "error": str(exc)})
                continue
            upstream_split = str(document.get("split") or path_split)
            model_id = stable_id("llmrouterbench", model_name)
            models[model_id] = {
                "model_id": model_id,
                "source": "llmrouterbench",
                "source_model_id": model_name,
                "provider": None,
                "display_name": model_name,
                "provenance_source_sha256": source_sha,
                "provenance_source_file": member,
            }
            records = document.get("records")
            if not isinstance(records, list):
                errors.append(
                    {"source_file": member, "record_index": "", "error": "records is not a list"}
                )
                continue
            evaluation_method = str(document.get("evaluation_method") or "upstream_unspecified")
            for position, raw in enumerate(records):
                try:
                    record = BenchmarkRecord.model_validate(raw)
                    query_text = record.origin_query or record.prompt
                    if query_text is None:
                        raise ValueError("record has neither origin_query nor prompt")
                    upstream_index = record.index if record.index is not None else position
                    query_id = stable_id(
                        "llmrouterbench", dataset, upstream_index, canonical_text(query_text)
                    )
                    queries.setdefault(
                        query_id,
                        {
                            "query_id": query_id,
                            "dataset": dataset,
                            "task_type": dataset,
                            "upstream_split": upstream_split,
                            "upstream_index": str(upstream_index),
                            "origin_query": query_text,
                            "prompt": record.prompt,
                            "ground_truth_json": _json(record.ground_truth),
                            "provenance_source_sha256": source_sha,
                            "provenance_source_file": member,
                            "provenance_record_index": position,
                        },
                    )
                    evaluation_id = stable_id(query_id, model_id, member, position)
                    if evaluation_id in seen_evaluations:
                        continue
                    seen_evaluations.add(evaluation_id)
                    known = set(BenchmarkRecord.model_fields)
                    extra = {k: v for k, v in raw.items() if k not in known}
                    evaluations.append(
                        {
                            "evaluation_id": evaluation_id,
                            "query_id": query_id,
                            "model_id": model_id,
                            "dataset": dataset,
                            "source_split": upstream_split,
                            "evaluation_method": evaluation_method,
                            "metric_name": "upstream_score",
                            "quality_score": record.score,
                            "prediction_json": _json(record.prediction),
                            "raw_output_json": _json(record.raw_output),
                            "prompt_tokens": record.prompt_tokens,
                            "completion_tokens": record.completion_tokens,
                            "historical_cost_usd": record.cost,
                            "aggregate_file_time_seconds": document.get("time_taken"),
                            "request_latency_seconds": None,
                            "source_extra_json": _json(extra),
                            "provenance_source_sha256": source_sha,
                            "provenance_source_file": member,
                            "provenance_record_index": position,
                        }
                    )
                    evaluation_count += 1
                    if len(evaluations) >= evaluation_batch_size:
                        writer = _write_batch(writer, temporary_evaluations, evaluations)
                except (ValidationError, ValueError, TypeError) as exc:
                    errors.append(
                        {"source_file": member, "record_index": str(position), "error": str(exc)}
                    )
        if evaluations:
            writer = _write_batch(writer, temporary_evaluations, evaluations)
        if writer is None:
            pq.write_table(
                pa.Table.from_pylist([], schema=EVALUATION_SCHEMA),
                temporary_evaluations,
                compression="zstd",
            )
        else:
            writer.close()
            writer = None
        temporary_evaluations.replace(evaluation_path)
    finally:
        if writer is not None:
            writer.close()

    frames = {
        "models": pd.DataFrame(models.values()),
        "queries": pd.DataFrame(queries.values()),
    }
    for name, frame in frames.items():
        frame.to_parquet(output_dir / f"{name}.parquet", index=False, compression="zstd")
    pd.DataFrame(errors, columns=["source_file", "record_index", "error"]).to_parquet(
        output_dir / "import_errors.parquet", index=False, compression="zstd"
    )
    return {
        "models": len(models),
        "queries": len(queries),
        "evaluations": evaluation_count,
        "errors": len(errors),
    }


def write_empty_future_tables(output_dir: Path) -> None:
    catalog_columns = [
        "snapshot_at",
        "source",
        "model_id",
        "canonical_slug",
        "provider",
        "display_name",
        "context_window_tokens",
        "input_modalities_json",
        "output_modalities_json",
        "supported_parameters_json",
        "input_usd_per_million_tokens",
        "output_usd_per_million_tokens",
        "raw_json",
    ]
    hardware_columns = [
        "measurement_id",
        "query_id",
        "model_id",
        "measured_at",
        "runtime",
        "model_artifact_id",
        "quantization",
        "cpu_model",
        "cpu_threads",
        "ram_total_bytes",
        "gpu_model",
        "gpu_count",
        "vram_total_bytes",
        "cold_start_seconds",
        "load_seconds",
        "time_to_first_token_seconds",
        "generation_seconds",
        "input_tokens",
        "output_tokens",
        "energy_joules",
        "success",
        "error_type",
        "provenance_json",
    ]
    for name, columns in {
        "model_catalog_snapshots": catalog_columns,
        "hardware_measurements": hardware_columns,
    }.items():
        path = output_dir / f"{name}.parquet"
        if not path.exists():
            pd.DataFrame(columns=columns).to_parquet(path, index=False)
