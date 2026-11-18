# Phase 3.6 — Independent Validation and Research Freeze

## Outcome

The routing research is frozen. No new architecture was introduced and no historical artifact was
modified. Preregistration preceded external-label discovery. No eligible independent benchmark
with the same exact eight-model panel exists under the zero-paid-inference constraint, so the
confirmatory hypothesis was not tested and all existing generalization conclusions remain
exploratory.

The final matched-budget audit reproduced the revised gate and historical controls. Revised gating
beats its semantic deterministic control at 75% and 100% budgets, but validation-constrained TF-IDF
is higher quality and cheaper at those operating points. Semantic MLP remains the closest learned
OOD alternative to Best Single, with substantial compute overhead and severe ARC calibration shift.

Standardized CPU results are: TF-IDF 1.51/1.81 ms single p50/p95; Sparse A .39/.64 ms; Semantic MLP
25.86/29.29 ms; revised gate 30.00/39.20 ms. These exclude downstream generation.

## Software verification and limitations

The audit adds persisted per-query gating decisions, 10,000-draw paired intervals, selection
distributions, training histories, Pareto visualization, frozen TF-IDF/gate artifacts, CPU timing,
and meaningful regression tests for missing labels, constant heads, checkpoint round-trips, and
paired statistics. Dataset validation, Ruff, pytest, and artifact/JSON checks are required before
closure. Experimental orchestration remains less unit-covered than core primitives; end-to-end
reproduction artifacts compensate but do not make line coverage a correctness guarantee. Final
verification passed 47 tests with one optional skip; total statement coverage is 55%, while
`semantic.py` improved from 39% to 66% coverage. Ruff and dataset validation are clean.

## Decision

**GO TO PHASE 4 WITH VALIDATION LIMITATIONS.** There is no engineering defect, leakage discovery,
or reproducibility failure that warrants blocking hardware measurement. Phase 4 may compare the
frozen routing baselines against real local latency and memory, while explicitly stating that
semantic robustness and revised gating lack independent confirmation. Phase 4 implementation was
not started in this phase.
