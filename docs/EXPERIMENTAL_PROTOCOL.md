# Experimental Protocol (Frozen Phase 2)

## Data and splits

Source SHA-256 is `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`.
Seed 3407 grouped splits are immutable: duplicate groups cannot cross train/validation/test. Train
fits models and expected costs; validation selects budget penalties; test is read once for final
evaluation. ARC-AGI is the OOD test.

Experiment A uses complete lightweight-20 panels and reports quality only; its historical monetary
cost is descriptive and does not include hardware. Experiment B uses complete proprietary-8 panels
and historical request costs. Experiment C uses the proprietary-8 ARC-AGI panel. ARC-AGI has 17
flagship observations per query but none of the lightweight models, so lightweight-20 OOD evaluation
is infeasible rather than silently changing the pool.

## Outcomes and access

Success is `quality_score >= 1`; mean upstream score is additionally retained. Results are reported
per dataset because evaluators are heterogeneous. Routers receive text, allowed models, optional
pre-inference task metadata, train-estimated cost, and constraints. They never receive current-query
scores, outputs, or actual output-token cost. Oracle is post-hoc and non-deployable.

The 20/8 pools were selected during Phase 1B using archive-wide coverage analysis, including test
coverage. This is a selection-bias risk. Phase 2 treats the pools as frozen and makes no population
claim; future confirmation needs a separately frozen dataset/pool.

Manifest hashes, configuration hashes, dependency versions, source version, seed, runtime and
artifacts are saved per run. Existing run directories cannot be overwritten.
