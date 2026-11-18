# Final Routing Comparison

| Router | Proprietary ID | ARC-AGI | Lightweight ID | CPU single p50/p95 | Interpretation |
|---|---:|---:|---:|---:|---|
| Best Single | .5994 | **.4275** | .6547 | negligible | Robust fixed control |
| TF-IDF | **.6155** | .2525 | .6778 | 1.51 / 1.81 ms | Best proprietary ID and upper-budget cost-quality control; brittle ARC shift |
| Sparse A | .6086 ± .0035 | .3600 ± .0677 | not rerun | **.39 / .64 ms** | Fastest learned router; intermediate OOD |
| Semantic MLP | .6042 ± .0050 | .4210 ± .0091 | **.6790 ± .0019** | 25.86 / 29.29 ms | Stronger shift robustness, no consistent ID win |
| Revised gate | .6130 at full budget | not evaluated | not evaluated | 30.00 / 39.20 ms | Fixes collapse; not better than constrained TF-IDF |

Semantic MLP's ARC advantage over TF-IDF is large but concentrated in one previously inspected task
family. Train-only leave-dataset-out Semantic Logistic beat fold-specific Best Single mainly on
ArenaHard, creative-writing, and coding, while losing on SimpleQA, HLE, MMLU-Pro, LiveCodeBench,
SWE-bench, math, tau2, and GPQA. This supports task-dependent robustness, not universal semantic
superiority. ARC ECE rose from .026 ID to .249 OOD, showing that routing improvement and calibrated
confidence are separate properties. Confidence fallback changes 12.8% of ARC selections and ends
exactly at Best Single quality; it primarily reproduces the fixed policy rather than detecting a
new robust routing regime.

CPU measurements use four threads, warmup, identical process/hardware, single-query distributions,
and batch 128. Batch throughputs were 2,777 q/s TF-IDF, 2,914 Sparse A, 46.1 Semantic MLP, and 41.2
revised gate. Checkpoints were 3.10 MB, 2.57 MB, 0.10 MB, and 0.11 MB respectively; semantic methods
also require the encoder and a 38.2 MB embedding cache for offline data. Loading was .121 s TF-IDF,
.0031 s Sparse, .403 s encoder+MLP, and .405 s encoder+gate. Absolute process RSS at measurement
points ranged from 1.06 to 1.29 GB; incremental RSS is allocator-state dependent. These are router-only measurements,
not downstream generation latency.
