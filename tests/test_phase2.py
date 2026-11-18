from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import adaptiveai.benchmark as benchmark_module
from adaptiveai.benchmark import (
    BenchmarkConfig,
    _complete_queries,
    run_benchmark,
    select_best_single,
)
from adaptiveai.normalize import normalize_archive
from adaptiveai.resolution import resolve_evaluations
from adaptiveai.routers import (
    CheapestRouter,
    FixedRouter,
    RandomRouter,
    RoutingRequest,
    TaskAwareRouter,
    TfidfSuccessRouter,
    oracle_decision,
)
from adaptiveai.statistics import bootstrap_mean_ci, paired_bootstrap_difference


def request() -> RoutingRequest:
    return RoutingRequest("q", "hello", ("a", "b"))


def test_random_router_is_reproducible() -> None:
    first, second = RandomRouter(7), RandomRouter(7)
    assert [first.route(request()).model_id for _ in range(20)] == [
        second.route(request()).model_id for _ in range(20)
    ]


def test_cheapest_rejects_missing_price_and_honors_budget() -> None:
    router = CheapestRouter({"a": 2.0})
    assert router.route(request()).model_id == "a"
    constrained = RoutingRequest("q", "hello", ("a", "b"), max_expected_cost=1.0)
    with pytest.raises(ValueError):
        router.route(constrained)


def test_oracle_uses_quality_then_minimum_cost() -> None:
    decision = oracle_decision({"a": 1.0, "b": 1.0}, {"a": 2.0, "b": 1.0})
    assert decision.model_id == "b"
    assert decision.diagnostics["post_hoc"]


def test_resolution_mean_preserves_missing_not_zero() -> None:
    frame = pd.DataFrame(
        [
            {
                "query_id": "q",
                "model_id": "m",
                "quality_score": 1.0,
                "historical_cost_usd": 1.0,
                "provenance_source_file": "b",
                "provenance_record_index": 1,
            },
            {
                "query_id": "q",
                "model_id": "m",
                "quality_score": np.nan,
                "historical_cost_usd": 3.0,
                "provenance_source_file": "a",
                "provenance_record_index": 1,
            },
        ]
    )
    result = resolve_evaluations(frame, "mean")
    assert result.quality_score.iloc[0] == 1.0
    assert result.historical_cost_usd.iloc[0] == 2.0
    assert result.repeat_count.iloc[0] == 2


def test_bootstrap_and_paired_comparison_known_fixture() -> None:
    frame = pd.DataFrame(
        {"duplicate_group_id": ["a", "b", "c"], "dataset": ["d"] * 3, "x": [1.0, 1.0, 1.0]}
    )
    assert bootstrap_mean_ci(frame, "x", samples=50) == (1.0, 1.0)
    left = pd.DataFrame({"query_id": ["a", "b"], "quality_score": [1.0, 1.0]})
    right = pd.DataFrame({"query_id": ["a", "b"], "quality_score": [0.0, 0.0]})
    assert paired_bootstrap_difference(left, right, samples=50) == (1.0, 1.0, 1.0)


def test_best_single_uses_only_supplied_training_matrix() -> None:
    train = pd.DataFrame({"a": [1.0, 1.0], "b": [0.0, 1.0]})
    test = pd.DataFrame({"a": [0.0], "b": [1.0]})
    assert select_best_single(train) == "a"
    assert select_best_single(test) == "b"


def test_complete_query_subset_is_comparable() -> None:
    frame = pd.DataFrame(
        {
            "query_id": ["q1", "q1", "q2"],
            "model_id": ["a", "b", "a"],
            "quality_score": [1.0, 0.0, 1.0],
        }
    )
    assert _complete_queries(frame, ("a", "b")) == {"q1"}


def test_routing_request_contains_no_current_query_label() -> None:
    assert "quality_score" not in RoutingRequest.__dataclass_fields__


def test_fixed_task_and_tfidf_routers() -> None:
    req = RoutingRequest("q", "python function", ("a", "b"), {"task_type": "coding"})
    assert FixedRouter("a").route(req).model_id == "a"
    assert TaskAwareRouter({"coding": "b"}, "a").route(req).model_id == "b"
    router = TfidfSuccessRouter(max_features=50).fit(
        ["python code", "write function", "history fact", "capital city"],
        {"a": np.array([1, 1, 0, 0]), "b": np.array([0, 0, 1, 1])},
        expected_costs={"a": 1.0, "b": 0.1},
    )
    assert router.route(req).model_id in {"a", "b"}
    router.set_cost_penalty(100)
    assert router.route(req).model_id == "b"


def test_end_to_end_benchmark_on_controlled_fixture(
    sample_archive: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    processed = tmp_path / "processed"
    normalize_archive(sample_archive, processed)
    queries = pd.read_parquet(processed / "queries.parquet")
    splits = pd.DataFrame(
        {
            "query_id": queries.query_id,
            "duplicate_group_id": queries.query_id,
            "split": ["train", "test"],
            "split_strategy": ["fixture", "fixture"],
            "random_seed": [1, 1],
            "near_duplicate_threshold": [0.92, 0.92],
        }
    )
    splits.to_parquet(processed / "data_splits.parquet", index=False)
    monkeypatch.setattr(benchmark_module, "LIGHTWEIGHT20", ("provider__small", "provider__strong"))
    output = run_benchmark(
        processed,
        tmp_path / "runs",
        BenchmarkConfig(random_repeats=1, bootstrap_samples=10, max_features=50),
    )
    summary = pd.read_parquet(output / "summary.parquet")
    assert {"best_single", "tfidf_logistic", "oracle_upper_bound"}.issubset(summary.router)
    with pytest.raises(FileExistsError):
        run_benchmark(
            processed,
            tmp_path / "runs",
            BenchmarkConfig(random_repeats=1, bootstrap_samples=10, max_features=50),
        )
