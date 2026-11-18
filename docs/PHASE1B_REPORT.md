# Phase 1B Report

## Engineering

The downloader now reuses hash-verified archives, preserves partial bytes, resumes via HTTP Range,
and retries transport failures. A real CDN disconnect validated this path. Two undocumented archive
path layouts are supported. Evaluations are written in 5,000-row Zstandard Parquet batches.

The OpenRouter parser now accepts structured `pricing.overrides` and treats observed `-1` fixed-price
sentinels as null while retaining raw JSON. The snapshot has 470 unique IDs from 69 provider
prefixes. Exact-only mapping correctly leaves all 40 benchmark names unresolved.

Near-duplicates use exact normalization plus task/number-constrained four-band SimHash blocking and
Jaccard 0.92 verification. Real processing used 12,525 candidates instead of roughly 347 million
all-pairs comparisons: 53.78 s, 410 MB peak RSS. Normalization took 175.34 s and 1.34 GB peak RSS;
EDA took 14.10 s and 847 MB peak RSS.

## Data and artifacts

- Archive: 1,283,503,080 bytes; SHA-256
  `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`.
- 700 JSON files; 548,059 source records; 548,046 accepted; 13 quarantined.
- 27 datasets, 40 models, 26,367 queries.
- 26,366 queries have at least five model results; median coverage is 20.
- 10,881 repeated query/model pairs and 237 score conflicts are explicitly reported.
- EDA generated coverage, quality, cost, performance, pairwise, and quality-cost artifacts without
  constructing a global model ranking.

## Decision

Real data are suitable for controlled quality-routing baselines on predeclared matched pools, but
not for hardware-aware claims. Scores are evaluator-specific, missingness is task/model-dependent,
most inputs are upstream evaluation splits, exact catalog identities remain unresolved, and
hardware measurements are absent.

**GO TO PHASE 2**, limited to per-benchmark quality and historical-monetary-cost baselines under the
documented split/matched-panel protocol. Hardware-aware claims remain blocked.
