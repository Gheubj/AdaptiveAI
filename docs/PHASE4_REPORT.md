# Phase 4 — Hardware-Aware Hybrid LLM Routing

## Engineering summary

Implemented hardware discovery, revision/hash-pinned local registry, llama.cpp CLI/server adapters,
streaming TTFT measurement, process lifecycle and timeout errors, eight deterministic policies,
quality/latency/memory separation, real end-to-end execution, local-only and cost constraints, mock
cloud abstraction, CLI commands, localhost HTTP API, structured provenance, profiling/quality
artifacts, and orchestration tests. Two real Q4_K_M models totaling 1.453 GB were used.

## Findings

Qwen loads in .528 s and uses .532 GB peak RSS; SmolLM2 loads in 1.704 s and uses 2.288 GB. Warm
long-workload p95 latency is .651 versus 1.694 s. Strict test quality ties at .25; post-hoc relaxed
answer containment is .875 versus .750. Consequently fixed Qwen dominates the measured strict
quality-latency-memory frontier. Hardware-aware routing selected SmolLM2 from validation quality and
was slower without a test gain. Latency prediction correctly orders the models, but the tiny sample
does not establish calibrated per-query latency prediction. Neural hardware routing was skipped for
insufficient data. Energy is N/A.

Model loading is material, especially for SmolLM2; keeping a model loaded eliminates that start
cost. Memory constraints below 2.288 GB change selection to Qwen. Actual concurrency-two improves
throughput but raises request latency. These measurements reproduce from raw Parquet files on this
host; general quality and hardware claims remain exploratory.

## Decision

**CONTINUE HARDWARE RESEARCH.** The inference system works and the negative comparison is credible
for its micro-panel, but eight held-out queries, two small models, strict-format sensitivity, and no
energy measurement are insufficient for a Product MVP claim. No hardware-aware superiority is
claimed.
