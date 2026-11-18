# Evidence Storage

Phase 6B uses standard-library SQLite through `EvidenceStore`. Rows contain searchable source,
source model ID, canonical provisional identity, benchmark, metric, reliability, retrieval time,
redistribution state, and the complete validated JSON evidence payload.

Exact evidence IDs are idempotent. A stable logical key combines source record, benchmark, metric,
source model/revision, and evaluation configuration. Repeated identical snapshot/value records are
unchanged; changed values or source versions are appended and reported as conflicts. Validated
history is never overwritten.

Queries support model, source model, benchmark, reliability, permission, provenance, and staleness.
Publication-safe export evaluates every record through the permission ledger. Unknown
redistribution yields no exported row; direct export raises `PermissionError` with reason codes.

Databases and raw snapshots live under ignored `data/evidence/` and `data/external_cache/`. Reads
are offline. SQLite is sufficient for the current single-process pilot; no service is introduced.
