from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

TOKEN_RE = re.compile(r"\w+", re.UNICODE)
NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


@dataclass(frozen=True)
class DuplicateDetectionStats:
    queries: int
    exact_merges: int
    candidate_pairs: int
    near_merges: int
    oversized_blocks_skipped: int


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.casefold()))


def jaccard_similarity(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if a or b else 0.0


def _number_signature(text: str) -> tuple[str, ...]:
    return tuple(NUMBER_RE.findall(text.casefold()))


def _simhash(text: str) -> int:
    tokens = TOKEN_RE.findall(text.casefold())
    features = (
        tokens if len(tokens) < 3 else [" ".join(tokens[i : i + 3]) for i in range(len(tokens) - 2)]
    )
    vector = [0] * 64
    for feature in set(features):
        value = int.from_bytes(hashlib.blake2b(feature.encode(), digest_size=8).digest(), "big")
        for bit in range(64):
            vector[bit] += 1 if value & (1 << bit) else -1
    return sum((1 << bit) for bit, weight in enumerate(vector) if weight >= 0)


def _simhash_blocks(value: int) -> tuple[tuple[int, int], ...]:
    """Four 16-bit bands: candidates must agree on at least one band."""
    return tuple((band, (value >> (band * 16)) & 0xFFFF) for band in range(4))


def duplicate_groups(
    queries: pd.DataFrame,
    threshold: float = 0.92,
    *,
    max_block_size: int = 500,
    return_stats: bool = False,
) -> dict[str, str] | tuple[dict[str, str], DuplicateDetectionStats]:
    ids = queries["query_id"].astype(str).tolist()
    texts = queries["origin_query"].fillna(queries.get("prompt", "")).astype(str).tolist()
    parent = list(range(len(ids)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    exact: dict[str, int] = {}
    exact_merges = 0
    for i, text in enumerate(texts):
        canonical = " ".join(text.casefold().split())
        if canonical in exact:
            union(i, exact[canonical])
            exact_merges += 1
        else:
            exact[canonical] = i

    blocks: defaultdict[tuple[str, tuple[str, ...], int, int], list[int]] = defaultdict(list)
    task_types = queries.get("task_type", pd.Series([""] * len(queries))).astype(str).tolist()
    for i, text in enumerate(texts):
        signature = _number_signature(text)
        for band, value in _simhash_blocks(_simhash(text)):
            blocks[(task_types[i], signature, band, value)].append(i)

    candidates: set[tuple[int, int]] = set()
    oversized = 0
    for members in blocks.values():
        if len(members) > max_block_size:
            oversized += 1
            continue
        for position, left in enumerate(members):
            for right in members[position + 1 :]:
                candidates.add((min(left, right), max(left, right)))

    near_merges = 0
    for i, j in sorted(candidates):
        if find(i) == find(j):
            continue
        # Numeric differences are a hard veto: 2+2 and 2+3 are not duplicates.
        if _number_signature(texts[i]) != _number_signature(texts[j]):
            continue
        if jaccard_similarity(texts[i], texts[j]) >= threshold:
            union(i, j)
            near_merges += 1
    groups: defaultdict[int, list[str]] = defaultdict(list)
    for i, query_id in enumerate(ids):
        groups[find(i)].append(query_id)
    mapping = {}
    for members in groups.values():
        group_id = hashlib.sha256("\x1f".join(sorted(members)).encode()).hexdigest()
        mapping.update(dict.fromkeys(members, group_id))
    stats = DuplicateDetectionStats(
        queries=len(ids),
        exact_merges=exact_merges,
        candidate_pairs=len(candidates),
        near_merges=near_merges,
        oversized_blocks_skipped=oversized,
    )
    return (mapping, stats) if return_stats else mapping


def _bucket(key: str, seed: int, train: float, validation: float) -> str:
    value = int(hashlib.sha256(f"{seed}:{key}".encode()).hexdigest()[:16], 16) / 2**64
    if value < train:
        return "train"
    if value < train + validation:
        return "validation"
    return "test"


def create_splits(
    queries: pd.DataFrame,
    seed: int = 3407,
    train: float = 0.7,
    validation: float = 0.15,
    near_duplicate_threshold: float = 0.92,
    holdout_task_types: set[str] | None = None,
) -> pd.DataFrame:
    if not (0 < train < 1 and 0 <= validation < 1 and train + validation < 1):
        raise ValueError("Invalid split ratios")
    holdout_task_types = holdout_task_types or set()
    groups = duplicate_groups(queries, near_duplicate_threshold)
    assert isinstance(groups, dict)
    rows = []
    for row in queries.itertuples(index=False):
        group_id = groups[str(row.query_id)]
        is_ood = str(row.task_type) in holdout_task_types
        rows.append(
            {
                "query_id": row.query_id,
                "duplicate_group_id": group_id,
                "split": "ood_test" if is_ood else _bucket(group_id, seed, train, validation),
                "split_strategy": "task_holdout" if is_ood else "group_hash",
                "random_seed": seed,
                "near_duplicate_threshold": near_duplicate_threshold,
            }
        )
    return pd.DataFrame(rows)
