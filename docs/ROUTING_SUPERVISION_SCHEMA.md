# Routing Supervision Schema

Phase 6B.5 keeps model-capability evidence and routing-supervision evidence separate.

`RoutingQuery` stores stable identity, original split, declared research role, task family/name,
native metric semantics, authorized content or reference, optional ground truth, and provenance.
`RoutingCandidate` retains source ID, optional exact AdaptiveAI identity, provider/deployment,
quantization, revision status, and a `historical_only` boundary. `RoutingOutcome` stores one matched
query/candidate result with native score, evaluation configuration, optional response, tokens,
latency, historical cost and price source, explicit missingness, provenance, and permissions.

Missing query/model pairs are absent cells reported by `MatrixAudit`; they are never converted to
failures or zero. Duplicate identical cells are counted; conflicting runs remain explicit. Scores
with different metric ID, units, scale, task protocol, or evaluation configuration cannot be pooled.

Historical source IDs may be used for offline research while remaining ineligible for live routing.
Unknown revision, provider configuration, or quantization is not inferred from a display name.
