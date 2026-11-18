import json
from pathlib import Path

import pandas as pd

from adaptiveai.audit import audit_archive, coverage_analysis
from adaptiveai.normalize import normalize_archive


def test_real_schema_audit_on_representative_fragment(sample_archive: Path, tmp_path: Path) -> None:
    output = tmp_path / "audit.json"
    result = audit_archive(sample_archive, output)
    assert result["files"] == 2
    assert result["records"] == 5
    assert result["datasets"] == {"math": 2}
    assert "string" in result["record_field_types"]["origin_query"]
    assert json.loads(output.read_text())["files"] == 2


def test_coverage_artifacts(sample_archive: Path, tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    normalize_archive(sample_archive, processed, evaluation_batch_size=1)
    summary = coverage_analysis(processed, tmp_path / "reports")
    assert summary["unique_queries"] == 2
    assert summary["unique_models"] == 2
    assert summary["queries_ge_2_models"] == 2
    pairwise = pd.read_parquet(tmp_path / "reports" / "model_pair_intersection.parquet")
    assert pairwise.to_numpy().max() == 2
