from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from adaptiveai.evidence import EvidenceRecord, EvidenceType, Reliability, SystemKind
from adaptiveai.identity import EvaluationSubject
from adaptiveai.permissions import SourcePermissions


class AdapterDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    adapter_id: str
    adapter_version: str
    source_id: str
    source_version: str
    permissions: SourcePermissions


class BenchmarkSourceAdapter(ABC):
    descriptor: AdapterDescriptor

    @abstractmethod
    def validate(self, payload: Any) -> None: ...

    @abstractmethod
    def normalize(self, payload: Any, subject: EvaluationSubject) -> tuple[EvidenceRecord, ...]: ...


class FixtureResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    benchmark: str
    benchmark_version: str
    task_distribution: str
    metric: str
    value: float
    units: str
    scale: str
    sample_size: int = Field(ge=1)
    retrieved_at: datetime


class FixtureBenchmarkAdapter(BenchmarkSourceAdapter):
    def __init__(self, descriptor: AdapterDescriptor):
        self.descriptor = descriptor

    def validate(self, payload: Any) -> None:
        if not isinstance(payload, list) or not payload:
            raise ValueError("fixture payload must be a non-empty list")
        for row in payload:
            FixtureResult.model_validate(row)

    def normalize(self, payload: Any, subject: EvaluationSubject) -> tuple[EvidenceRecord, ...]:
        self.validate(payload)
        records = []
        for raw in payload:
            row = FixtureResult.model_validate(raw)
            records.append(
                EvidenceRecord(
                    evidence_type=EvidenceType.EXTERNAL_AGGREGATE,
                    source_id=self.descriptor.source_id,
                    source_version=self.descriptor.source_version,
                    retrieved_at=row.retrieved_at,
                    subject=subject,
                    system_kind=SystemKind.BASE_MODEL,
                    benchmark=row.benchmark,
                    benchmark_version=row.benchmark_version,
                    task_distribution=row.task_distribution,
                    method=f"{self.descriptor.adapter_id}@{self.descriptor.adapter_version}",
                    metric=row.metric,
                    value=row.value,
                    units=row.units,
                    scale=row.scale,
                    sample_size=row.sample_size,
                    provenance=(self.descriptor.adapter_id,),
                    reliability=Reliability.DECLARED,
                    permissions=self.descriptor.permissions,
                )
            )
        return tuple(records)
