# Phase 3.6 Preregistration

Frozen on 2026-11-18 before acquiring or inspecting any new candidate benchmark labels.

## Hypotheses and comparisons

The primary hypothesis is that the frozen five-seed Semantic MLP has higher paired query-level
success than TF-IDF Logistic on an independent, overlap-screened query distribution with the same
eight exact model versions. The primary estimand is the mean success difference, averaged across
seeds without treating seeds as queries. Success requires a positive point estimate whose
cluster-bootstrap 95% interval excludes zero. Secondary, explicitly exploratory comparisons are
Semantic MLP versus Best Single; Sparse A versus TF-IDF; and revised trainable gate versus the
validation-selected deterministic selector at each of four frozen budgets. Failure to satisfy the
primary criterion is a valid negative result.

## Frozen candidates

1. Best Single selected on the original training split.
2. TF-IDF Logistic: Phase 2 configuration, word 1–2 grams, 30,000 features, `C=1`, seed 3407.
3. Sparse Neural A: 20,000 deterministic hash buckets, 32-dimensional EmbeddingBag, 64-hidden MLP,
   checkpoints in `reports/phase3/proprietary8-main`, seeds 3407–3411. SHA-256 prefixes:
   `a494c166`, `25f35a32`, `ad4676ad`, `ed53017c`, `4545415f`.
4. Semantic MLP: frozen MiniLM revision
   `c9745ed1d9f207416be6d2e6f8de32d1f16199bf`, 384→64→8 head, checkpoints in
   `reports/phase3_5/proprietary8`, seeds 3407–3411. SHA-256 prefixes: `23735e43`, `8ae0f0a0`,
   `60df5e57`, `8441c9ea`, `b844c657`.
5. Revised primal-dual trainable constrained gate exactly as implemented in Phase 3.5.
6. Validation-selected deterministic constrained selector using the same semantic quality forecasts.

No architecture, encoder, objective, hidden width, threshold, or checkpoint may be changed in
response to confirmatory labels. Original Architecture C, Cheapest, and cost-constrained TF-IDF are
audit controls, not primary candidates.

## Eligible independent data

An eligible benchmark must predate this preregistration or have independently collected real
query/model outcomes; expose query-level prompts and documented scores; have research-compatible
terms; contain at least 500 overlap-free queries after exact and near-duplicate screening; and
match all eight exact proprietary model versions for direct frozen-policy evaluation. A model name
without an exact version/provider match is not overlap. Standard benchmark-family reuse is recorded
and weakens independence even when prompt overlap is absent.

If the model pool differs, only query-distribution transfer of frozen representations can be tested;
new output heads constitute adaptation and are labeled exploratory retraining. Such results cannot
satisfy the primary hypothesis. No paid inference or synthetic replacement labels are allowed.

## Metrics and statistics

Primary metric: binary query success at the source benchmark's documented scoring threshold.
Secondary metrics: mean native score, per-dataset success, model-selection distribution, avoidable
failure, regret to oracle, and mean historical cost only when costs and model versions are
comparable. Use paired cluster bootstrap over duplicate/near-duplicate groups (10,000 resamples,
seed 3407). Report absolute and relative differences, per-seed variability separately, and no
unadjusted significance claims for secondary comparisons.

The gating audit retains budgets at 25/50/75/100% of train-selected Best Single historical cost.
Report realized cost, quality, quality/cost, any-query and mean-cost violation, selection shares,
and paired intervals. No test-based penalty or winner selection is permitted.

## Exclusions and decision rule

Exclude missing prompts, unresolved model versions, undocumented scores, duplicated prompts after
retaining one duplicate group, and queries lacking the complete required model panel. Record every
exclusion. Do not impute outcomes. If eligibility fails, perform no confirmatory test and state that
independent validation is unavailable.

Phase 4 may proceed with validation limitations if software, leakage, and reproducibility audits
pass; absence of a neural win is not an engineering blocker. Phase 4 is blocked only for a concrete
defect that invalidates trustworthy downstream measurement.
