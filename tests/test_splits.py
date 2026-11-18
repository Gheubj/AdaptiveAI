import pandas as pd

from adaptiveai.splits import create_splits, duplicate_groups, jaccard_similarity


def queries() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "query_id": "a",
                "origin_query": "Explain red green blue colors",
                "prompt": None,
                "task_type": "general",
            },
            {
                "query_id": "b",
                "origin_query": "explain red green blue colors!",
                "prompt": None,
                "task_type": "general",
            },
            {
                "query_id": "c",
                "origin_query": "Solve x plus one",
                "prompt": None,
                "task_type": "math",
            },
            {
                "query_id": "d",
                "origin_query": "Write Python code",
                "prompt": None,
                "task_type": "code",
            },
        ]
    )


def test_split_reproducibility_and_no_duplicate_leakage() -> None:
    first = create_splits(queries(), seed=42)
    second = create_splits(queries(), seed=42)
    pd.testing.assert_frame_equal(first, second)
    assert (
        first.set_index("query_id").loc["a", "split"]
        == first.set_index("query_id").loc["b", "split"]
    )
    assert first.groupby("duplicate_group_id").split.nunique().max() == 1


def test_ood_task_holdout() -> None:
    result = create_splits(queries(), holdout_task_types={"code"})
    assert result.set_index("query_id").loc["d", "split"] == "ood_test"


def test_similarity() -> None:
    assert jaccard_similarity("a b c", "a b c") == 1.0
    assert jaccard_similarity("a b", "x y") == 0.0


def test_numeric_lookalikes_are_not_duplicates() -> None:
    frame = pd.DataFrame(
        [
            {"query_id": "x", "origin_query": "What is 2 + 2?", "task_type": "math"},
            {"query_id": "y", "origin_query": "What is 2 + 3?", "task_type": "math"},
        ]
    )
    groups = duplicate_groups(frame, threshold=0.5)
    assert isinstance(groups, dict)
    assert groups["x"] != groups["y"]


def test_case_and_whitespace_duplicates_are_merged() -> None:
    frame = pd.DataFrame(
        [
            {"query_id": "x", "origin_query": "Explain   blue light", "task_type": "science"},
            {"query_id": "y", "origin_query": " explain blue light ", "task_type": "science"},
        ]
    )
    groups, stats = duplicate_groups(frame, return_stats=True)
    assert groups["x"] == groups["y"]
    assert stats.exact_merges == 1
