# Routing Feasibility

## Matched coverage

- 26,367 queries, 40 models, and 27 datasets.
- 26,366 queries have results from at least 2, 3, and 5 models.
- Models per query: minimum 1, median 20, maximum 38.
- LiveCodeBench (1,055), GPQA (198), and AIME (60) have 38-model panels.
- A stable 20-model lightweight pool covers the same 15,541 queries.
- Eight proprietary models share an identical 14,760-query panel. Adding Claude Sonnet 4 leaves
  14,759; a 12-model extended pool leaves 13,521.
- Sparse version IDs (`claude-opus-4.1`, `glm-4.6-3888`) should not enter the primary pool.

## Preliminary baselines

Per-dataset artifacts were generated for the lightweight-20 pool (22 eligible datasets) and
proprietary-8 pool (13). Always Strongest and Always Cheapest are selected on routing-train queries
only; Random uses seed 3407; Oracle uses test labels solely as a retrospective ceiling. Repeated
upstream observations are excluded.

No cross-dataset aggregate is a scientific result because evaluator semantics differ. Results are
in `routing_feasibility_small20.parquet` and `routing_feasibility_proprietary8.parquet`.

Phase 2 should begin with lightweight-20 for quality routing and a secondary proprietary-8 cost
experiment. Rules and hyperparameters must use train/validation only. Rule-Based routing was not
optimized here because that would begin Phase 2. Hardware-aware conclusions remain infeasible
until local latency/load/memory/energy measurements exist.
