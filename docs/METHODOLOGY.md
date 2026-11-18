# Methodology

## Research question

Does hardware-aware, quality-constrained routing improve the quality/cost/latency trade-off over
quality-only and rule-based routing in local, cloud, and hybrid deployment? Phase 1 establishes the
data needed to test this question; it does not test the hypothesis itself.

## Data lineage

Every import records source ID/URI, UTC retrieval time, byte size, SHA-256, filename, and importer
version. Raw archives are immutable. Normalized rows include source hash, source member path, and
record position. Invalid records are quarantined in `import_errors.parquet` rather than silently
dropped.

## Tables

- `models.parquet`: source-scoped model identities.
- `queries.parquet`: stable query identity, dataset/task metadata, text, and ground truth.
- `evaluations.parquet`: query-model score/output/token/cost observations.
- `model_catalog_snapshots.parquet`: point-in-time catalog and current-price observations.
- `data_splits.parquet`: deterministic grouped assignments.
- `hardware_measurements.parquet`: empty Phase 4-ready measurement contract.

JSON-valued fields are serialized explicitly so schemas remain stable across heterogeneous tasks.

## Comparability protocol

Primary comparisons must be conducted on matched query panels: the same query set and eligible
model pool for all methods. Report coverage and missingness. Aggregate only within compatible
metric definitions; cross-task summaries require predeclared normalization and weighting. Oracle
is a retrospective upper bound using observed candidates, not a deployable system.

## Splits

The default seed is 3407. Query IDs and detected near-duplicate groups are indivisible. A stable
hash yields 70/15/15 train/validation/test assignment. Specified task types bypass this split and
enter `ood_test`. Leakage validation asserts that a duplicate group appears in exactly one split.

Phase 1B uses exact normalized hashing plus four SimHash bands within task and numeric-token blocks,
followed by token Jaccard >=0.92. Different numeric signatures are never merged. Oversized blocks
are skipped rather than risking quadratic behavior. ARC-AGI is the current task-level OOD holdout.

## EDA

EDA reports query/model counts, dataset distribution, missingness, duplicated query-model pairs,
model coverage per query, fully covered matched panels, and score summaries by dataset. Plots are
descriptive only; they do not establish model superiority.

Preliminary baselines select fixed models using train only, evaluate test per benchmark, exclude
repeated upstream observations, and reserve Oracle labels solely for a retrospective ceiling.

## Phase 2 routing benchmark

The primary matrix averages repeated observations per query/model cell; representative and exclude
policies are sensitivity analyses. Deployable routers cannot access current-query outcomes. One
regularized logistic success model is fitted per candidate on sparse TF-IDF features. Success is a
score of one; heterogeneous mean upstream scores remain separate. Confidence intervals use a
dataset-stratified duplicate-group bootstrap, and comparisons are paired on identical queries.

## Phase 3 neural protocol

Each neural example is one query with its masked model-outcome vector, so every query has equal loss
weight. Hashed word inputs exclude answers, responses, benchmark identity, actual completion cost,
test labels, and OOD labels. Early stopping and temperature scaling use validation only. Five seeds
measure training variability. Test and ARC-AGI were previously inspected and remain exploratory.
Train-only leave-dataset-out folds provide a separate transfer diagnostic.

## Phase 3.5 semantic protocol

Frozen normalized MiniLM embeddings feed independent logistic heads, an independent-head MLP, and a
shared learned model-embedding scorer. Validation selects early stopping, fallback threshold, and
deterministic budget multipliers. Five seeds measure trainable-head variation. Query sampling uses
paired bootstrap; seeds are summarized separately and never treated as independent queries.

## Phase 4 systems methodology

Profiling uses pinned llama.cpp, six CPU threads, context 2,048, deterministic generation, streaming
TTFT, three process starts, ten warm repetitions per workload, and concurrency blocks. Quality uses
a frozen objective train/validation/test panel with identical prompts for both models. Routing uses
development estimates; held-out outcomes are never decision features.
# Phase 4.5 local methodology

Before Phase 4.5 inference, a 500-query V2 protocol, split, typed scoring rules, model pool,
parameters, policies, exclusions, and success criteria were frozen. All local models received every
query with temperature zero and seed 3407. Train outcomes fit predictors, validation selected model
and hyperparameters, and test was evaluated once. Query bootstrap preserves query independence;
McNemar uses paired discordances. Repeated hardware requests quantify execution variability and do
not enlarge the query sample. Offline counterfactual policy evaluation and actual lifecycle-aware
execution are reported separately.
