# Neural Routing Results

Five-seed proprietary-8 results:

| Router | ID success mean ± SD | Mean historical cost | ARC-AGI | Gain vs TF-IDF ID |
|---|---:|---:|---:|---:|
| Phase 2 Best Single | 0.5994 | 0.06049 | 0.4275 | -0.0161 |
| Phase 2 TF-IDF | **0.6155** | 0.03906 | 0.2525 | 0 |
| Sparse A | 0.6086 ± 0.0035 | 0.05094 | **0.3600 ± 0.0677** | -0.0069 |
| Shared B | 0.5986 ± 0.0072 | 0.04752 | 0.3095 ± 0.0396 | -0.0169 |
| Trainable Gate C | 0.4339 ± 0.0052 | **0.00102** | 0.1295 ± 0.0021 | -0.1816 |
| Deterministic constrained B | 0.5462 ± 0.0035 | 0.00132 | 0.2240 ± 0.0283 | -0.0694 |
| Phase 2 Oracle | 0.7896 | 0.00620 | 0.5350 | +0.1741 |

Paired 95% cluster intervals versus TF-IDF on ID are [-0.0198, 0.0060] for A, [-0.0301,
-0.0043] for B, and [-0.2047, -0.1588] for C. A is statistically inconclusive relative to TF-IDF;
B and C are worse in this exploratory comparison.

A/B checkpoints are about 2.57/2.59 MB. Mean training is 18.3/20.0 s per seed. Single-query CPU
p50/p95 latency is 0.057/0.095 ms for A and 0.140/0.226 ms for B. C's gate is 16.9 KB, takes 22.0 s
to train in the seed-3407 resource run, and with B has p50/p95 0.194/0.369 ms. These are router-only
measurements, not LLM latency.
