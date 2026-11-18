from pathlib import Path

import pandas as pd

from adaptiveai.feasibility import evaluate_preliminary_baselines
from adaptiveai.normalize import normalize_archive
from adaptiveai.splits import create_splits


def test_feasibility_uses_train_selected_baselines(sample_archive: Path, tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    normalize_archive(sample_archive, processed)
    queries = pd.read_parquet(processed / "queries.parquet")
    splits = create_splits(queries, seed=1, train=0.5, validation=0.0)
    # The tiny hash split can put both queries together; use non-leaking singleton groups.
    splits["split"] = ["train", "test"]
    splits["duplicate_group_id"] = splits.query_id
    splits.to_parquet(processed / "data_splits.parquet", index=False)
    result = evaluate_preliminary_baselines(
        processed,
        tmp_path / "result.parquet",
        ["provider__small", "provider__strong"],
        seed=1,
    )
    assert set(result.strategy) == {
        "always_strongest_train_selected",
        "always_cheapest_train_selected",
        "random_seeded",
        "quality_oracle_min_cost_tiebreak",
    }
