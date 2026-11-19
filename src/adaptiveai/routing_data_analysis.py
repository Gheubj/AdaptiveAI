from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from itertools import combinations

from pydantic import BaseModel, ConfigDict

from adaptiveai.routing_supervision import RoutingDatasetSnapshot, RoutingOutcome, RoutingQuery


class AnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MatrixAudit(AnalysisModel):
    query_count: int
    candidate_count: int
    outcome_count: int
    expected_pairs: int
    missing_pairs: tuple[tuple[str, str], ...]
    exact_duplicates: int
    conflicting_duplicates: tuple[tuple[str, str], ...]
    incompatible_metric_rows: tuple[str, ...]


def audit_matrix(snapshot: RoutingDatasetSnapshot) -> MatrixAudit:
    queries = {item.query_id: item for item in snapshot.queries}
    candidates = {item.candidate_id for item in snapshot.candidates}
    cells: dict[tuple[str, str], list[RoutingOutcome]] = defaultdict(list)
    incompatible: list[str] = []
    for outcome in snapshot.outcomes:
        key = (outcome.query_id, outcome.candidate_id)
        cells[key].append(outcome)
        query = queries[outcome.query_id]
        if (outcome.metric_id, outcome.metric_units, outcome.metric_scale) != (
            query.metric_id,
            query.metric_units,
            query.metric_scale,
        ):
            incompatible.append(outcome.outcome_id)
    exact_duplicates = 0
    conflicts: list[tuple[str, str]] = []
    for key, values in cells.items():
        if len(values) <= 1:
            continue
        signatures = {
            (item.score, item.evaluation.fingerprint, item.historical_cost_usd) for item in values
        }
        if len(signatures) == 1:
            exact_duplicates += len(values) - 1
        else:
            conflicts.append(key)
    missing = tuple(
        sorted(
            (query_id, candidate_id)
            for query_id in queries
            for candidate_id in candidates
            if (query_id, candidate_id) not in cells
        )
    )
    return MatrixAudit(
        query_count=len(queries),
        candidate_count=len(candidates),
        outcome_count=len(snapshot.outcomes),
        expected_pairs=len(queries) * len(candidates),
        missing_pairs=missing,
        exact_duplicates=exact_duplicates,
        conflicting_duplicates=tuple(sorted(conflicts)),
        incompatible_metric_rows=tuple(sorted(incompatible)),
    )


def deterministic_query_sample(
    queries: tuple[RoutingQuery, ...], *, maximum: int, seed: int
) -> tuple[RoutingQuery, ...]:
    ordered = sorted(
        queries,
        key=lambda query: hashlib.sha256(f"{seed}:{query.query_id}".encode()).hexdigest(),
    )
    return tuple(ordered[:maximum])


class LeakageAudit(AnalysisModel):
    exact_cross_split: tuple[tuple[str, str], ...]
    repeated_query_ids: tuple[str, ...]
    confirmatory_valid: bool
    limitations: tuple[str, ...]


def audit_leakage(queries: tuple[RoutingQuery, ...]) -> LeakageAudit:
    by_hash: dict[str, list[RoutingQuery]] = defaultdict(list)
    id_counts: dict[str, int] = defaultdict(int)
    for query in queries:
        id_counts[query.query_id] += 1
        if query.content_hash:
            by_hash[query.content_hash].append(query)
    overlaps: set[tuple[str, str]] = set()
    for values in by_hash.values():
        for left, right in combinations(values, 2):
            if left.split != right.split:
                overlaps.add(tuple(sorted((left.query_id, right.query_id))))
    repeated = tuple(sorted(key for key, count in id_counts.items() if count > 1))
    roles = {query.data_role for query in queries}
    return LeakageAudit(
        exact_cross_split=tuple(sorted(overlaps)),
        repeated_query_ids=repeated,
        confirmatory_valid=not overlaps
        and not repeated
        and any(role.value == "confirmatory_test" for role in roles),
        limitations=(
            "exact normalized-text hashes only; semantic or upstream training overlap may remain",
        ),
    )


class CandidatePerformance(AnalysisModel):
    candidate_id: str
    mean_score: float
    observed_queries: int
    missing_rate: float
    mean_latency_seconds: float | None
    mean_cost_usd: float | None


class PairwiseComplementarity(AnalysisModel):
    left: str
    right: str
    common_queries: int
    left_only_success: int
    right_only_success: int
    both_success: int
    neither_success: int


class HeadroomAnalysis(AnalysisModel):
    metric_id: str
    query_count: int
    candidate_performance: tuple[CandidatePerformance, ...]
    best_single_candidate: str
    best_single_quality: float
    oracle_quality: float
    oracle_gain: float
    cheapest_candidate: str | None
    cheapest_quality: float | None
    fastest_candidate: str | None
    fastest_quality: float | None
    oracle_quality_ci95: tuple[float, float] | None
    pairwise: tuple[PairwiseComplementarity, ...]


def analyze_binary_headroom(
    snapshot: RoutingDatasetSnapshot, *, bootstrap_samples: int = 1000, seed: int = 3407
) -> HeadroomAnalysis:
    audit = audit_matrix(snapshot)
    if audit.conflicting_duplicates or audit.incompatible_metric_rows:
        raise ValueError("headroom analysis requires conflict-free compatible outcomes")
    outcomes = [item for item in snapshot.outcomes if item.metric_units == "binary"]
    if not outcomes:
        raise ValueError("no compatible binary outcomes")
    metric_ids = {item.metric_id for item in outcomes}
    if len(metric_ids) != 1:
        raise ValueError("binary headroom cannot combine different metrics")
    query_ids = sorted({item.query_id for item in outcomes})
    candidate_ids = sorted({item.candidate_id for item in outcomes})
    matrix = {(item.query_id, item.candidate_id): item for item in outcomes}
    performance: list[CandidatePerformance] = []
    for candidate_id in candidate_ids:
        values = [
            matrix[(query, candidate_id)] for query in query_ids if (query, candidate_id) in matrix
        ]
        performance.append(
            CandidatePerformance(
                candidate_id=candidate_id,
                mean_score=sum(item.score for item in values) / len(values),
                observed_queries=len(values),
                missing_rate=1 - len(values) / len(query_ids),
                mean_latency_seconds=_mean_known(item.latency_seconds for item in values),
                mean_cost_usd=_mean_known(item.historical_cost_usd for item in values),
            )
        )
    best = max(performance, key=lambda item: (item.mean_score, item.candidate_id))
    complete_queries = [
        query
        for query in query_ids
        if all((query, candidate) in matrix for candidate in candidate_ids)
    ]
    if not complete_queries:
        raise ValueError("oracle analysis requires at least one fully matched query")
    oracle_values = [
        max(matrix[(query, candidate)].score for candidate in candidate_ids)
        for query in complete_queries
    ]
    oracle_quality = sum(oracle_values) / len(oracle_values)
    cheapest = _lowest_known(performance, "mean_cost_usd")
    fastest = _lowest_known(performance, "mean_latency_seconds")
    pairwise = []
    for left, right in combinations(candidate_ids, 2):
        common = [
            query for query in query_ids if (query, left) in matrix and (query, right) in matrix
        ]
        pairwise.append(
            PairwiseComplementarity(
                left=left,
                right=right,
                common_queries=len(common),
                left_only_success=sum(
                    matrix[(q, left)].score > 0 and matrix[(q, right)].score == 0 for q in common
                ),
                right_only_success=sum(
                    matrix[(q, right)].score > 0 and matrix[(q, left)].score == 0 for q in common
                ),
                both_success=sum(
                    matrix[(q, left)].score > 0 and matrix[(q, right)].score > 0 for q in common
                ),
                neither_success=sum(
                    matrix[(q, left)].score == 0 and matrix[(q, right)].score == 0 for q in common
                ),
            )
        )
    interval = _bootstrap_mean_interval(oracle_values, bootstrap_samples, seed)
    return HeadroomAnalysis(
        metric_id=next(iter(metric_ids)),
        query_count=len(complete_queries),
        candidate_performance=tuple(performance),
        best_single_candidate=best.candidate_id,
        best_single_quality=best.mean_score,
        oracle_quality=oracle_quality,
        oracle_gain=oracle_quality - best.mean_score,
        cheapest_candidate=cheapest.candidate_id if cheapest else None,
        cheapest_quality=cheapest.mean_score if cheapest else None,
        fastest_candidate=fastest.candidate_id if fastest else None,
        fastest_quality=fastest.mean_score if fastest else None,
        oracle_quality_ci95=interval,
        pairwise=tuple(pairwise),
    )


class OracleCostHeadroom(AnalysisModel):
    quality_floor: float
    feasible: bool
    best_fixed_candidate: str | None
    best_fixed_mean_cost_usd: float | None
    posthoc_oracle_mean_cost_usd: float | None
    limitation: str


def analyze_oracle_cost(
    snapshot: RoutingDatasetSnapshot, *, quality_floor: float
) -> OracleCostHeadroom:
    outcomes = snapshot.outcomes
    if any(item.historical_cost_usd is None for item in outcomes):
        return OracleCostHeadroom(
            quality_floor=quality_floor,
            feasible=False,
            best_fixed_candidate=None,
            best_fixed_mean_cost_usd=None,
            posthoc_oracle_mean_cost_usd=None,
            limitation="historical prices are incomplete; current prices were not substituted",
        )
    by_candidate: dict[str, list[RoutingOutcome]] = defaultdict(list)
    by_query: dict[str, list[RoutingOutcome]] = defaultdict(list)
    for item in outcomes:
        by_candidate[item.candidate_id].append(item)
        by_query[item.query_id].append(item)
    feasible_fixed = []
    for candidate, values in by_candidate.items():
        quality = sum(item.score for item in values) / len(values)
        cost = sum(item.historical_cost_usd or 0 for item in values) / len(values)
        if quality >= quality_floor:
            feasible_fixed.append((cost, candidate))
    oracle_costs = []
    for values in by_query.values():
        eligible = [item for item in values if item.score >= quality_floor]
        if eligible:
            oracle_costs.append(min(item.historical_cost_usd or 0 for item in eligible))
    if not feasible_fixed or len(oracle_costs) != len(by_query):
        return OracleCostHeadroom(
            quality_floor=quality_floor,
            feasible=False,
            best_fixed_candidate=None,
            best_fixed_mean_cost_usd=None,
            posthoc_oracle_mean_cost_usd=None,
            limitation="quality floor is not feasible for every query/fixed candidate",
        )
    fixed_cost, fixed_candidate = min(feasible_fixed)
    return OracleCostHeadroom(
        quality_floor=quality_floor,
        feasible=True,
        best_fixed_candidate=fixed_candidate,
        best_fixed_mean_cost_usd=fixed_cost,
        posthoc_oracle_mean_cost_usd=sum(oracle_costs) / len(oracle_costs),
        limitation="post-hoc oracle bound; not an achievable routing savings claim",
    )


def _mean_known(values) -> float | None:
    known = [value for value in values if value is not None]
    return sum(known) / len(known) if known else None


def _lowest_known(
    performance: list[CandidatePerformance], field: str
) -> CandidatePerformance | None:
    known = [item for item in performance if getattr(item, field) is not None]
    return min(known, key=lambda item: (getattr(item, field), item.candidate_id)) if known else None


def _bootstrap_mean_interval(
    values: list[float], samples: int, seed: int
) -> tuple[float, float] | None:
    if not values or samples < 1:
        return None
    generator = random.Random(seed)
    estimates = sorted(
        sum(generator.choice(values) for _ in values) / len(values) for _ in range(samples)
    )
    low = estimates[int(0.025 * (samples - 1))]
    high = estimates[int(0.975 * (samples - 1))]
    return low, high
