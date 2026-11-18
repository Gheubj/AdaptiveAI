from pathlib import Path

from adaptiveai.eda import run_eda
from adaptiveai.normalize import normalize_archive


def test_eda_writes_reproducible_artifacts(sample_archive: Path, tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    report = tmp_path / "report"
    normalize_archive(sample_archive, processed)
    summary = run_eda(processed, report)
    assert summary["unique_queries"] == 2
    assert (report / "coverage_heatmap.png").exists()
    assert (report / "model_performance_by_benchmark.parquet").exists()
    assert (report / "pairwise_model_comparisons.parquet").exists()
