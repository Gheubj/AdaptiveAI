# Matched Outcome Analysis

The implemented audit constructs an explicit `Query × Candidate → Outcome` matrix and reports
expected/observed cells, missing pairs, exact duplicates, conflicting duplicates, and native-metric
incompatibilities. Deterministic query sampling hashes `seed:query_id`, so sampling is independent of
model performance and input order.

For one compatible binary metric, the analysis reports per-model quality, missingness, known mean
latency/cost, Best Single, Cheapest/Fastest when supported, post-hoc Oracle, bootstrap uncertainty,
and pairwise left-only/right-only/both/neither success counts. It refuses conflicting cells or mixed
metrics.

Only synthetic fixtures were analyzed in Phase 6B.5. No xRouteBench or RoutingCompendium Best Single,
Oracle, complementarity, latency, or cost result is claimed. Previously published AdaptiveAI results
remain historical and non-confirmatory.
