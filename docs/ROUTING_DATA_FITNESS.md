# Routing Data Fitness

| Criterion | xRouteBench | RoutingCompendium | Existing AdaptiveAI research |
|---|---|---|---|
| Matched per-query outcomes | Dense, 18 deployments | Dense lists, 10–112 models | Dense enough after filtering |
| Responses/tokens/latency | Yes | Generally performance only | Responses present; latency not request-level |
| Cost | Historical provider prices | Mixed provider price/size proxy | Historical cost with limitations |
| Native splits | Train/test; raw queries add validation | Benchmark-as-split | Frozen research splits |
| Task diversity | High | High, heterogeneous | 27 datasets |
| Exact revisions | Incomplete | Mostly incomplete | Unresolved externally |
| Unseen-model research | Limited fixed pool | Potentially strong across pools | Previously studied fixed pools |
| Permission fitness | Blocked: no dataset license | Blocked per split | Local research only; no redistribution |
| Independent confirmation | Potential future source | Potential future source | No; repeatedly inspected |

xRouteBench is the best technical fit for task-, prompt-, cost-, and latency-aware routing. It is not
currently permission-fit. RoutingCompendium is valuable for cross-pool/model-conditioned research,
but its component licensing and metric heterogeneity demand split-specific review. Existing data can
support method development but not a fresh confirmatory claim.

Decision: **BLOCKED BY DATA RIGHTS / DATA QUALITY** for a new real pilot. Continue with contracts,
tests, and preregistration; do not manufacture statistics from public dataset-card summaries.
