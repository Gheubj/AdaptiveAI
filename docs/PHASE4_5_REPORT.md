# Phase 4.5 Report — Local Benchmark Expansion and Hardware Validation

## Engineering and benchmark summary

Phase 4.5 froze a 500-query panel (150/100/250) spanning six objective task families, validated a
task-aware scorer on 14 manually specified cases, and executed 1,000 matched local generations.
The run is resumable. An uncaught localhost timeout was discovered after 132 rows, fixed, tested,
and the run resumed without recomputation. Five model-query requests ultimately have recorded
failure status across all splits. No paid API, cloud GPU, extra model download, or generated-code
execution was used.

Final verification: 65 tests passed, one optional real-archive integration test was skipped, Ruff
and formatting checks passed, processed-data validation passed, and total statement coverage is
78%. Critical timeout, crashed-process, failed-load, unavailable-model, local-only, insufficient
RAM, and no-feasible-model paths have explicit tests.

| Model | Test quality | 95% CI | p50 | p95 | Peak RAM |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-0.5B Q4_K_M | .172 | [.128,.220] | .409 s | 1.023 s | .532 GB |
| SmolLM2-1.7B Q4_K_M | .416 | [.356,.480] | .919 s | 1.886 s | 2.288 GB |

SmolLM2's paired gain over Qwen is statistically supported on this frozen panel. Improved scoring
changes the Phase 4 apparent tie, but the workloads differ, so it does not retroactively invalidate
or replace Phase 4.

## Complementarity and routing

Both/only-Qwen/only-Smol/neither counts are 41/2/63/144. Oracle quality is .424 and adds only .008
over Fixed Strongest. Fixed Strongest, TF-IDF, Semantic, and Hardware-Aware all score .416. Offline
Task-Aware also scores .416 with lower response latency, but real switching reverses its latency
advantage: 16 switches add 24.79 s on a 24-query matched subset. Hardware-aware feasibility works,
yet does not improve quality over the persistent strongest model.

## Scientific interpretation

1. The models disagree, but useful complementarity is almost entirely SmolLM2 over Qwen.
2. Query-dependent routing does not outperform Fixed Strongest in quality; it does outperform Fixed
   Fastest because it mostly selects Strongest.
3. Hardware-aware routing has no demonstrated superior quality–latency trade-off after lifecycle
   cost is included.
4. Switching is material and dominates microsecond-scale router overhead.
5. Task-aware scoring reveals a real quality difference hidden by the Phase 4 strict micro-panel.
6. SmolLM2 versus Qwen quality is statistically supported for this panel. Oracle headroom and
   lifecycle comparisons remain workload-specific; real execution has only 24 queries.
7. Generalization beyond locally templated tasks, energy, sustained concurrency, and any third model
   remain exploratory or unmeasured.
8. The primary scientific limit is the two-model pool with only .008 oracle gain above Strongest.

## Decision

**GO TO PHASE 5 WITH RESEARCH LIMITATIONS.** The system is ready to be packaged as an experimental,
local-only open-source tool because inference, constraints, provenance, recovery, and reproducible
evaluation work. It is not production ready, and the release must not claim that adaptive routing
beats a persistent strongest-model baseline. Phase 5 was not started.
