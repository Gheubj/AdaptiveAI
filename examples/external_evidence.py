"""Phase 6B evidence workflow. Offline by default; pass --live for one bounded HF request."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from adaptiveai.evidence_comparison import compare_models
from adaptiveai.evidence_store import EvidenceStore
from adaptiveai.external_intelligence import (
    build_external_profile,
    coverage_report,
    profile_summary,
    write_private_snapshot,
)
from adaptiveai.hf_benchmark import HuggingFaceLimits, HuggingFaceSWEVerifiedAdapter
from adaptiveai.identity_resolution import IdentityResolver


def fixture() -> bytes:
    return json.dumps(
        [
            {
                "rank": 1,
                "filename": ".eval_results/example.yaml",
                "value": 50.0,
                "verified": False,
                "source": {"url": "https://huggingface.co/example/model"},
                "modelId": "example/model",
                "lower_is_better": False,
            }
        ]
    ).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="perform one anonymous HF API request")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--directory", type=Path, default=Path("data/external_cache/phase6b"))
    args = parser.parse_args()
    adapter = HuggingFaceSWEVerifiedAdapter(
        HuggingFaceLimits(max_results=args.max_results, total_request_limit=1, retry_limit=0)
    )
    result = (
        adapter.fetch_and_import()
        if args.live
        else adapter.import_bytes(fixture(), retrieved_at=datetime(2026, 11, 18, tzinfo=UTC))
    )
    resolutions = tuple(
        IdentityResolver().resolve(record.source_model_id or "") for record in result.records
    )
    write_private_snapshot(result, args.directory)
    with EvidenceStore(args.directory / "evidence.sqlite3") as store:
        update = store.ingest(result.records)
        first = store.query(source_model_id=result.records[0].source_model_id)
    profile = build_external_profile(result.records[0])
    output = {
        "manifest": result.manifest.model_dump(mode="json"),
        "coverage": coverage_report(result, resolutions).model_dump(mode="json"),
        "store_update": update.__dict__,
        "profile": profile_summary(profile, result.records),
        "provenance": list(result.records[0].provenance),
        "identity_resolution": resolutions[0].model_dump(mode="json"),
        "self_comparison": compare_models(first, first).model_dump(mode="json"),
    }
    print(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
