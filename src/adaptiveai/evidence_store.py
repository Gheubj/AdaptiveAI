from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from adaptiveai.evidence import EvidenceRecord, Reliability
from adaptiveai.permissions import PermissionState, evaluate_export


@dataclass(frozen=True)
class StoreUpdate:
    inserted: int
    unchanged: int
    conflicts: int


class EvidenceStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                logical_key TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_version TEXT NOT NULL,
                source_model_id TEXT,
                model_id TEXT NOT NULL,
                benchmark TEXT,
                metric TEXT,
                reliability TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                redistribution TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_model ON evidence(model_id)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_evidence_benchmark ON evidence(benchmark)"
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> EvidenceStore:
        return self

    def __exit__(self, *_args) -> None:
        self.close()

    @staticmethod
    def logical_key(record: EvidenceRecord) -> str:
        return "|".join(
            (
                record.source_id,
                record.source_record_id or "unknown-record",
                record.benchmark or "unknown-benchmark",
                record.metric or "unknown-metric",
                record.source_model_id or record.subject.model.canonical_id,
                record.subject.model.revision.revision or "revision-unknown",
                record.subject.configuration.fingerprint,
            )
        )

    def ingest(self, records: tuple[EvidenceRecord, ...], *, dry_run: bool = False) -> StoreUpdate:
        inserted = unchanged = conflicts = 0
        for record in records:
            existing = self.connection.execute(
                "SELECT evidence_id FROM evidence WHERE evidence_id = ?", (record.evidence_id,)
            ).fetchone()
            if existing:
                unchanged += 1
                continue
            logical_key = self.logical_key(record)
            prior = self.connection.execute(
                "SELECT payload FROM evidence WHERE logical_key = ? "
                "ORDER BY retrieved_at DESC LIMIT 1",
                (logical_key,),
            ).fetchone()
            if prior is not None:
                prior_record = EvidenceRecord.model_validate_json(prior["payload"])
                if (
                    prior_record.source_version == record.source_version
                    and prior_record.value == record.value
                ):
                    unchanged += 1
                    continue
                conflicts += 1
            if not dry_run:
                self.connection.execute(
                    """INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.evidence_id,
                        logical_key,
                        record.source_id,
                        record.source_version,
                        record.source_model_id,
                        record.subject.model.canonical_id,
                        record.benchmark,
                        record.metric,
                        record.reliability.value,
                        record.retrieved_at.isoformat(),
                        record.permissions.redistribution.value,
                        record.model_dump_json(),
                    ),
                )
                inserted += 1
        if not dry_run:
            self.connection.commit()
        else:
            inserted = len(records) - unchanged
        return StoreUpdate(inserted, unchanged, conflicts)

    def query(
        self,
        *,
        model_id: str | None = None,
        source_model_id: str | None = None,
        benchmark: str | None = None,
        reliability: Reliability | None = None,
        redistribution: PermissionState | None = None,
    ) -> tuple[EvidenceRecord, ...]:
        clauses: list[str] = []
        values: list[str] = []
        for column, value in (
            ("model_id", model_id),
            ("source_model_id", source_model_id),
            ("benchmark", benchmark),
            ("reliability", reliability.value if reliability else None),
            ("redistribution", redistribution.value if redistribution else None),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                values.append(value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self.connection.execute(
            "SELECT payload FROM evidence" + where + " ORDER BY retrieved_at, evidence_id", values
        ).fetchall()
        return tuple(EvidenceRecord.model_validate_json(row["payload"]) for row in rows)

    def stale(
        self, *, older_than_days: int, now: datetime | None = None
    ) -> tuple[EvidenceRecord, ...]:
        now = now or datetime.now(UTC)
        cutoff = (now - timedelta(days=older_than_days)).isoformat()
        rows = self.connection.execute(
            "SELECT payload FROM evidence WHERE retrieved_at < ?", (cutoff,)
        ).fetchall()
        return tuple(EvidenceRecord.model_validate_json(row["payload"]) for row in rows)

    def publication_safe_export(self) -> list[dict]:
        output = []
        for record in self.query():
            decision = evaluate_export(record.permissions)
            if decision.allowed:
                output.append(json.loads(record.model_dump_json()))
        return output

    def export_record(self, evidence_id: str) -> dict:
        row = self.connection.execute(
            "SELECT payload FROM evidence WHERE evidence_id = ?", (evidence_id,)
        ).fetchone()
        if row is None:
            raise KeyError(evidence_id)
        record = EvidenceRecord.model_validate_json(row["payload"])
        decision = evaluate_export(record.permissions)
        if not decision.allowed:
            raise PermissionError(
                f"evidence is not publication-safe: {', '.join(decision.reasons)}"
            )
        return json.loads(record.model_dump_json())
