from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx
import pandas as pd

from adaptiveai.schemas import OpenRouterModel

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def usd_per_token_to_per_million(value: str | float | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = Decimal(str(value))
        # OpenRouter currently emits -1 for router/meta-models without a fixed token price.
        # Preserve the sentinel in raw_json, but do not expose it as a negative USD price.
        if parsed < 0:
            return None
        return float(parsed * Decimal(1_000_000))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid price: {value!r}") from exc


def fetch_catalog(output_dir: Path, api_key: str | None = None) -> tuple[Path, Path]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        response = client.get(OPENROUTER_MODELS_URL, headers=headers)
        response.raise_for_status()
        payload = response.json()
    retrieved_at = datetime.now(UTC)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    raw_path = output_dir / f"openrouter-models-{stamp}.json"
    raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rows = []
    for raw in payload.get("data", []):
        model = OpenRouterModel.model_validate(raw)
        provider = model.id.split("/", 1)[0] if "/" in model.id else None
        rows.append(
            {
                "snapshot_at": retrieved_at,
                "source": "openrouter",
                "model_id": model.id,
                "canonical_slug": model.canonical_slug,
                "provider": provider,
                "display_name": model.name,
                "context_window_tokens": model.context_length,
                "input_modalities_json": json.dumps(
                    (model.architecture or {}).get("input_modalities", [])
                ),
                "output_modalities_json": json.dumps(
                    (model.architecture or {}).get("output_modalities", [])
                ),
                "supported_parameters_json": json.dumps(model.supported_parameters),
                "input_usd_per_million_tokens": usd_per_token_to_per_million(
                    model.pricing.get("prompt")
                ),
                "output_usd_per_million_tokens": usd_per_token_to_per_million(
                    model.pricing.get("completion")
                ),
                "raw_json": json.dumps(raw, sort_keys=True),
            }
        )
    parquet_path = output_dir / f"model-catalog-{stamp}.parquet"
    pd.DataFrame(rows).to_parquet(parquet_path, index=False)
    return raw_path, parquet_path


def exact_model_mapping(source_model_id: str, catalog: pd.DataFrame) -> str | None:
    """Map identifiers only by exact ID or canonical slug; never fuzzy-merge models."""
    candidates = catalog.loc[
        (catalog["model_id"] == source_model_id) | (catalog["canonical_slug"] == source_model_id),
        "model_id",
    ].drop_duplicates()
    return candidates.iloc[0] if len(candidates) == 1 else None


def write_mapping_report(
    benchmark_models: pd.DataFrame, catalog: pd.DataFrame, output: Path
) -> pd.DataFrame:
    rows = []
    for source_id in sorted(benchmark_models["source_model_id"].dropna().unique()):
        matched = exact_model_mapping(str(source_id), catalog)
        rows.append(
            {
                "llmrouterbench_model_id": source_id,
                "openrouter_model_id": matched,
                "mapping_status": "exact" if matched else "unresolved",
                "mapping_rule": "exact_id_or_canonical_slug" if matched else None,
                "review_note": None
                if matched
                else "No exact identity established; fuzzy merge prohibited",
            }
        )
    frame = pd.DataFrame(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output, index=False)
    return frame
