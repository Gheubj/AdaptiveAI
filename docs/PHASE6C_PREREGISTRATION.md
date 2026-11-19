# Phase 6C Preregistration — Benchmark-Informed Routing Baselines

Status: prepared, not executed.

## Research question

Does pre-inference query information plus compatible model profiles improve held-out cost at a
prespecified quality floor over simple fixed/rule/benchmark baselines in a complementary model pool?

## Inputs and targets

Allowed features are query text/features, task metadata available before inference, immutable model
profiles, deployment availability, and hard constraints. Responses, scores, labels, post-inference
tokens/latency, test aggregates, and candidate identity leakage are prohibited features. Targets are
native compatible quality, historical cost, observed latency, and explicit uncertainty/abstention.

## Baselines

Fixed Cheapest, Fixed Strongest, Fixed Fastest, Random, task-category rules, benchmark ranking,
TF-IDF, frozen semantic embeddings, model-conditioned estimator, and post-hoc Oracle. Each baseline
must pass `baseline_eligibility`; unsupported cost/latency/profile methods are reported unavailable.

## Evaluation

- source-native train/validation/test plus group-aware duplicate handling;
- ID holdout, OOD task/dataset, unseen family, leave-one-model-out, and temporal holdout where valid;
- hyperparameters selected on train/validation only;
- fixed final test once; no ARC-AGI/test selection;
- quality/cost/latency/missingness, paired effect intervals, calibration/abstention, overhead;
- Fixed Pool and Model-Conditioned approaches evaluated separately.

Hiding a model ID while retaining its outcomes in aggregate profile features is not unseen-model
generalization. GO requires identity-resolved, permission-fit matched data and measurable oracle
headroom. Otherwise continue data research.
