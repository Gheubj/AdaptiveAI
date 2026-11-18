from pathlib import Path

import pandas as pd

from adaptiveai.normalize import normalize_archive, write_empty_future_tables
from adaptiveai.splits import create_splits
from adaptiveai.validation import validate_dataset


def test_valid_dataset(sample_archive: Path, tmp_path: Path) -> None:
    output = tmp_path / "processed"
    normalize_archive(sample_archive, output)
    queries = pd.read_parquet(output / "queries.parquet")
    create_splits(queries).to_parquet(output / "data_splits.parquet", index=False)
    write_empty_future_tables(output)
    assert validate_dataset(output) == []


def test_leakage_is_detected(sample_archive: Path, tmp_path: Path) -> None:
    output = tmp_path / "processed"
    normalize_archive(sample_archive, output)
    queries = pd.read_parquet(output / "queries.parquet")
    splits = create_splits(queries)
    splits["duplicate_group_id"] = "same"
    splits.loc[splits.index[0], "split"] = "train"
    splits.loc[splits.index[1], "split"] = "test"
    splits.to_parquet(output / "data_splits.parquet", index=False)
    assert "splits: duplicate group leakage detected" in validate_dataset(output)
