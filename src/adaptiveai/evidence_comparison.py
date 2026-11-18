from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from adaptiveai.evidence import EvidenceRecord, Reliability, compare_evidence


class ComparablePair(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    left_evidence_id: str
    right_evidence_id: str
    benchmark: str
    metric: str
    left_value: float | int | str | bool
    right_value: float | int | str | bool
    left_reliability: Reliability
    right_reliability: Reliability
    limitations: tuple[str, ...]


class ModelComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    comparable: tuple[ComparablePair, ...]
    incompatible: tuple[str, ...]
    left_only: tuple[str, ...]
    right_only: tuple[str, ...]


def compare_models(
    left: tuple[EvidenceRecord, ...], right: tuple[EvidenceRecord, ...]
) -> ModelComparison:
    pairs: list[ComparablePair] = []
    incompatible: list[str] = []
    matched_left: set[str] = set()
    matched_right: set[str] = set()
    for left_record in left:
        for right_record in right:
            if (left_record.benchmark, left_record.metric) != (
                right_record.benchmark,
                right_record.metric,
            ):
                continue
            diagnostic = compare_evidence(left_record, right_record)
            if (
                diagnostic.comparable
                and left_record.value is not None
                and right_record.value is not None
            ):
                pairs.append(
                    ComparablePair(
                        left_evidence_id=left_record.evidence_id,
                        right_evidence_id=right_record.evidence_id,
                        benchmark=left_record.benchmark or "unknown",
                        metric=left_record.metric or "unknown",
                        left_value=left_record.value,
                        right_value=right_record.value,
                        left_reliability=left_record.reliability,
                        right_reliability=right_record.reliability,
                        limitations=(
                            "aggregate score; no per-prompt probability or significance inference",
                        ),
                    )
                )
                matched_left.add(left_record.evidence_id)
                matched_right.add(right_record.evidence_id)
            else:
                incompatible.append(
                    f"{left_record.evidence_id}:{right_record.evidence_id}:"
                    + ",".join(diagnostic.mismatches)
                )
    return ModelComparison(
        comparable=tuple(pairs),
        incompatible=tuple(sorted(incompatible)),
        left_only=tuple(
            record.evidence_id for record in left if record.evidence_id not in matched_left
        ),
        right_only=tuple(
            record.evidence_id for record in right if record.evidence_id not in matched_right
        ),
    )
