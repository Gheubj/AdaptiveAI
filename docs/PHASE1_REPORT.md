# Phase 1 Report

## Acquired data

No full research archive was downloaded in this session. Official source structure and metadata
were inspected, and a loader was implemented. Therefore real counts, missingness, coverage, model
rankings, and costs are not reported.

## Implemented foundation

The project now supports immutable local archive import; optional explicit OpenRouter catalog
retrieval; validated normalization to six research tables; error quarantine; provenance; exact
model identity mapping; cost-unit conversion; deterministic query-group splits; near-duplicate and
task-holdout mechanisms; leakage/schema validation; EDA plots and JSON summaries; and JSONL run
records. Offline tests cover all critical transformations.

## Feasibility assessment

- **Always Small/Cheapest:** feasible only after defining the candidate pool and joining historical
  price observations without substituting current prices.
- **Always Strong:** feasible as a best-single baseline selected on training data, not test data.
- **Random:** feasible with fixed seed and the same eligible candidate set per query.
- **Rule-Based:** feasible after predeclaring features/rules and handling missing candidates.
- **Neural Quality Router:** structurally feasible if matched query-model coverage is adequate;
  actual adequacy remains unverified without the archive.
- **Oracle:** feasible as a retrospective observed-candidate ceiling, with tie and missingness rules.

Hardware-aware comparison is not yet feasible: the benchmark does not establish reproducible
per-request local latency, cold-load cost, memory use, energy, or hardware/software configuration.
The prepared hardware schema captures these missing measurements.

## Phase 2 entry criteria

Freeze a validated real-data manifest; resolve metric semantics and licensing; quantify matched
coverage; document exclusions; create train-only baseline selection; and register every run.
