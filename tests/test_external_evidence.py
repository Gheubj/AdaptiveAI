from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from adaptiveai import cli
from adaptiveai.evidence import Reliability
from adaptiveai.evidence_comparison import compare_models
from adaptiveai.evidence_store import EvidenceStore
from adaptiveai.external_intelligence import (
    build_external_profile,
    coverage_report,
    profile_summary,
    snapshot_changed,
    write_private_snapshot,
)
from adaptiveai.hf_benchmark import (
    BenchmarkImportError,
    HuggingFaceLimits,
    HuggingFaceSWEVerifiedAdapter,
    ImportErrorCode,
)
from adaptiveai.identity import ModelFamily, ModelIdentity, ProviderAlias, ProviderIdentity
from adaptiveai.identity_resolution import IdentityResolver, ResolutionStatus

NOW = datetime(2026, 11, 18, tzinfo=UTC)


def row(model="org/model", value=50.0, **updates):
    payload = {
        "rank": 1,
        "filename": ".eval_results/result.yaml",
        "value": value,
        "verified": False,
        "source": {"url": f"https://huggingface.co/{model}", "name": "model card"},
        "pullRequest": 7,
        "modelId": model,
        "lower_is_better": False,
    }
    payload.update(updates)
    return payload


def imported(rows=None, **limit_updates):
    adapter = HuggingFaceSWEVerifiedAdapter(HuggingFaceLimits(**limit_updates))
    return adapter.import_bytes(json.dumps(rows or [row()]).encode(), retrieved_at=NOW)


def test_mocked_api_is_bounded_and_normalizes_original_values():
    payload = json.dumps([row(), row("other/model", 42.5)]).encode()
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, content=payload))
    result = HuggingFaceSWEVerifiedAdapter(
        HuggingFaceLimits(max_results=1, retry_limit=0)
    ).fetch_and_import(transport=transport)
    assert result.manifest.source_records == 2
    assert result.manifest.incomplete
    assert len(result.records) == 1
    record = result.records[0]
    assert (record.value, record.units, record.scale) == (50.0, "percent", "0..100")
    assert record.source_model_id == "org/model"
    assert record.subject.model.revision.revision is None
    assert record.reliability == Reliability.DECLARED


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(429), ImportErrorCode.RATE_LIMIT),
        (httpx.Response(500), ImportErrorCode.HTTP),
    ],
)
def test_structured_http_errors(response, code):
    transport = httpx.MockTransport(lambda _request: response)
    with pytest.raises(BenchmarkImportError) as caught:
        HuggingFaceSWEVerifiedAdapter(HuggingFaceLimits(retry_limit=0)).fetch_and_import(
            transport=transport
        )
    assert caught.value.code == code


def test_response_limit_malformed_empty_and_partial_schema():
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, content=b"[]" * 600))
    with pytest.raises(BenchmarkImportError) as caught:
        HuggingFaceSWEVerifiedAdapter(HuggingFaceLimits(max_download_bytes=1024)).fetch_and_import(
            transport=transport
        )
    assert caught.value.code == ImportErrorCode.RESPONSE_TOO_LARGE
    for raw, expected in ((b"{", ImportErrorCode.MALFORMED_JSON), (b"[]", ImportErrorCode.EMPTY)):
        with pytest.raises(BenchmarkImportError) as caught:
            HuggingFaceSWEVerifiedAdapter().import_bytes(raw)
        assert caught.value.code == expected
    result = imported([row(), {"rank": 2, "modelId": "broken"}])
    assert (len(result.records), len(result.diagnostics)) == (1, 1)
    assert result.manifest.incomplete


def test_identity_resolution_never_fuzzy_merges_and_handles_alias_ambiguity():
    model = ModelIdentity(family=ModelFamily(namespace="org", family="model"), model="model")
    provider = ProviderIdentity(provider_id="hf")
    alias = ProviderAlias(provider=provider, alias="org/model", model=model)
    assert (
        IdentityResolver(aliases=(alias,)).resolve("org/model").status
        == ResolutionStatus.VERIFIED_ALIAS
    )
    assert (
        IdentityResolver(models=(model,)).resolve("Org Model").status == ResolutionStatus.UNRESOLVED
    )
    other = ModelIdentity(family=ModelFamily(namespace="org", family="other"), model="other")
    ambiguous = IdentityResolver(
        aliases=(alias, ProviderAlias(provider=provider, alias="org/model", model=other))
    ).resolve("org/model")
    assert ambiguous.status == ResolutionStatus.AMBIGUOUS


def test_store_deduplicates_preserves_conflicts_queries_staleness_and_denies_export(tmp_path):
    first = imported().records[0]
    changed = imported([row(value=51.0)]).records[0]
    with EvidenceStore(tmp_path / "evidence.sqlite3") as store:
        assert store.ingest((first,)).inserted == 1
        assert store.ingest((first,)).unchanged == 1
        update = store.ingest((changed,))
        assert (update.inserted, update.conflicts) == (1, 1)
        assert len(store.query(source_model_id="org/model")) == 2
        assert len(store.query(benchmark="SWE-bench Verified")) == 2
        assert len(store.stale(older_than_days=1, now=NOW + timedelta(days=2))) == 2
        assert store.publication_safe_export() == []
        with pytest.raises(PermissionError, match="redistribution_unknown"):
            store.export_record(first.evidence_id)


def test_snapshot_profile_coverage_and_comparison(tmp_path):
    result = imported([row(), row("other/model", 42.5)])
    raw_path, manifest_path = write_private_snapshot(result, tmp_path)
    assert raw_path.read_bytes() == result.raw_bytes
    assert manifest_path.exists()
    write_private_snapshot(result, tmp_path)
    assert snapshot_changed("new", "old")
    different_time = HuggingFaceSWEVerifiedAdapter().import_bytes(
        result.raw_bytes, retrieved_at=NOW + timedelta(seconds=1)
    )
    with pytest.raises(FileExistsError, match="manifest collision"):
        write_private_snapshot(different_time, tmp_path)
    resolutions = tuple(
        IdentityResolver().resolve(record.source_model_id or "") for record in result.records
    )
    coverage = coverage_report(result, resolutions)
    assert coverage.accepted_records == 2
    assert coverage.unresolved_models == 2
    assert coverage.unknown_revisions == 2
    assert coverage.complete_provenance == 2
    assert coverage.verified_records == 0
    profile = build_external_profile(result.records[0])
    summary = profile_summary(profile, result.records)
    assert summary["known_results"] == 1
    assert "exact_model_revision" in summary["unknown_capabilities"]
    comparison = compare_models((result.records[0],), (result.records[1],))
    assert len(comparison.comparable) == 1
    incompatible = result.records[1].model_copy(update={"scale": "0..1"})
    comparison = compare_models((result.records[0],), (incompatible,))
    assert not comparison.comparable
    assert comparison.incompatible


def test_intelligence_cli_lists_sources_and_imports_offline_snapshot(tmp_path, capsys):
    assert cli.main(["intelligence", "sources"]) == 0
    assert "SWE-bench_Verified" in capsys.readouterr().out
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_bytes(json.dumps([row()]).encode())
    store = tmp_path / "store.sqlite3"
    cache = tmp_path / "cache"
    assert (
        cli.main(
            [
                "intelligence",
                "import",
                "--snapshot",
                str(snapshot),
                "--store",
                str(store),
                "--cache-dir",
                str(cache),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["update"]["inserted"] == 1
    assert (
        cli.main(
            ["intelligence", "evidence", "--store", str(store), "--source-model-id", "org/model"]
        )
        == 0
    )
    assert len(json.loads(capsys.readouterr().out)) == 1


@pytest.mark.live_hf
@pytest.mark.skipif(os.getenv("ADAPTIVEAI_LIVE_HF") != "1", reason="set ADAPTIVEAI_LIVE_HF=1")
def test_opt_in_live_hf_metadata():
    result = HuggingFaceSWEVerifiedAdapter(
        HuggingFaceLimits(max_results=1, retry_limit=0, total_request_limit=1)
    ).fetch_and_import()
    assert result.records
    assert result.manifest.size_bytes <= 1_048_576
