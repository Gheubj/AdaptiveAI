# Routing Dataset Adapter

`RoutingDatasetAdapter` is source-neutral. It exposes a permission-bearing descriptor, split
discovery, and bounded ingestion into an immutable `RoutingDatasetSnapshot`. Limits cover bytes,
queries, candidates, and outcomes. Source-specific implementations must preserve native splits,
metrics, IDs, missing values, and provenance.

Phase 6B.5 implements only `FixtureRoutingDatasetAdapter`, because neither audited external source
has sufficient row-level permission documentation. The fixture exercises parsing, bounds, partial
imports, candidate/query references, permissions, and snapshot checksums without resembling or
redistributing an external dataset.

An xRouteBench adapter may be added after permission clarification. It must map every source config
through the general schema rather than embedding xRouteBench assumptions in the schema itself.
Ordinary tests remain offline, and external downloads must stay outside Git/package artifacts.
