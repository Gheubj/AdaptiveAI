from pathlib import Path

import pandas as pd

from adaptiveai.normalize import infer_path_metadata, normalize_archive


def test_real_release_path_is_supported() -> None:
    assert infer_path_metadata("bench-release/aime/model-x/run.json") == (
        "aime",
        "unspecified",
        "model-x",
    )
    assert infer_path_metadata("bench-release/arcc/test/model-x/run.json") == (
        "arcc",
        "test",
        "model-x",
    )


def test_normalization_and_invalid_record_capture(sample_archive: Path, tmp_path: Path) -> None:
    output = tmp_path / "processed"
    counts = normalize_archive(sample_archive, output)
    assert counts == {"models": 2, "queries": 2, "evaluations": 4, "errors": 1}
    evaluations = pd.read_parquet(output / "evaluations.parquet")
    assert evaluations.evaluation_id.is_unique
    assert evaluations.request_latency_seconds.isna().all()
    assert set(evaluations.aggregate_file_time_seconds) == {12.0, 20.0}


def test_query_ids_match_across_models(sample_archive: Path, tmp_path: Path) -> None:
    output = tmp_path / "processed"
    normalize_archive(sample_archive, output)
    evaluations = pd.read_parquet(output / "evaluations.parquet")
    assert evaluations.groupby("query_id").model_id.nunique().tolist() == [2, 2]
