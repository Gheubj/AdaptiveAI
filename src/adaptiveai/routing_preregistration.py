from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BaselineName(StrEnum):
    FIXED_CHEAPEST = "fixed_cheapest"
    FIXED_STRONGEST = "fixed_strongest"
    FIXED_FASTEST = "fixed_fastest"
    RANDOM = "random"
    TASK_RULES = "task_category_rules"
    BENCHMARK_RANK = "benchmark_model_ranking"
    TFIDF = "tfidf"
    SEMANTIC = "semantic_embeddings"
    MODEL_CONDITIONED = "model_conditioned_estimator"
    ORACLE = "oracle_upper_bound"


class BaselineDataAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_count: int = Field(ge=0)
    matched_quality: bool = False
    historical_cost: bool = False
    observed_latency: bool = False
    task_labels: bool = False
    query_text: bool = False
    capability_profiles: bool = False
    compatible_aggregate_benchmarks: bool = False


class BaselineEligibility(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    baseline: BaselineName
    eligible: bool
    missing_requirements: tuple[str, ...]
    posthoc_only: bool = False


def baseline_eligibility(
    baseline: BaselineName, data: BaselineDataAvailability
) -> BaselineEligibility:
    requirements: dict[BaselineName, tuple[tuple[str, bool], ...]] = {
        BaselineName.FIXED_CHEAPEST: (("historical_cost", data.historical_cost),),
        BaselineName.FIXED_STRONGEST: (("matched_quality", data.matched_quality),),
        BaselineName.FIXED_FASTEST: (("observed_latency", data.observed_latency),),
        BaselineName.RANDOM: (("at_least_two_candidates", data.candidate_count >= 2),),
        BaselineName.TASK_RULES: (
            ("task_labels", data.task_labels),
            ("matched_quality", data.matched_quality),
        ),
        BaselineName.BENCHMARK_RANK: (
            ("compatible_aggregate_benchmarks", data.compatible_aggregate_benchmarks),
        ),
        BaselineName.TFIDF: (
            ("query_text", data.query_text),
            ("matched_quality", data.matched_quality),
        ),
        BaselineName.SEMANTIC: (
            ("query_text", data.query_text),
            ("matched_quality", data.matched_quality),
        ),
        BaselineName.MODEL_CONDITIONED: (
            ("query_text", data.query_text),
            ("matched_quality", data.matched_quality),
            ("capability_profiles", data.capability_profiles),
            ("at_least_two_candidates", data.candidate_count >= 2),
        ),
        BaselineName.ORACLE: (("matched_quality", data.matched_quality),),
    }
    missing = tuple(name for name, available in requirements[baseline] if not available)
    return BaselineEligibility(
        baseline=baseline,
        eligible=not missing,
        missing_requirements=missing,
        posthoc_only=baseline == BaselineName.ORACLE,
    )
