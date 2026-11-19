# Evidence and Provenance Schema

`EvidenceRecord` represents provider metadata, aggregate or per-instance external evaluations,
local evaluations, latency, cost, and capability claims. Every record stores source and source
version, retrieval time, exact evaluation subject, system kind, method, metric/value/units/scale,
sample size, provenance links, reliability, permissions, and explicit missing fields.

Missing source version, metric, value, or units must have a `MissingValue` reason. A field cannot
simultaneously have a value and a missing declaration. Content-addressed evidence IDs are SHA-256
hashes of canonical JSON; exact duplicates are rejected.

## Comparability

`compare_evidence` checks benchmark, benchmark version, task distribution, metric, units, scale,
harness, harness version, the complete evaluation-configuration hash, exact model revision, and
system kind. It returns structured mismatches. Incomparability is information, not an exception and
not permission to create a universal ranking. Routed systems, provider deployments, and base models
remain distinct.

The foundation deliberately provides no cross-benchmark aggregate score and no fabricated quality
or confidence field.
