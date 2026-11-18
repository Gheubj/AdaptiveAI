# Phase 3.5 — Semantic Representations and Robust Routing

## Status and protocol

Phase 3.5 is complete. Configuration was frozen before the repeated evaluation: the existing
grouped train/validation/test/ARC splits, MiniLM revision
`c9745ed1d9f207416be6d2e6f8de32d1f16199bf`, 384-dimensional normalized embeddings, independent
binary success heads, a 384→64 MLP, a 32-dimensional shared model embedding, five seeds
(3407–3411), and validation-only fallback/budget selection. Test and ARC-AGI had already been
inspected in Phases 2–3; every result below is exploratory, not confirmatory. No test/ARC labels
entered fitting, threshold selection, or budget selection.

## Main results

| Router | Proprietary-8 ID quality | Seed SD | Mean historical cost | ARC-AGI | Lightweight-20 ID |
|---|---:|---:|---:|---:|---:|
| Best Single | 0.5994 | — | 0.0609 | **0.4275** | 0.6547 |
| TF-IDF (Phase 2) | **0.6155** | — | 0.0391 | 0.2525 | 0.6778 |
| Sparse A (Phase 3) | 0.6086 | 0.0035 | — | 0.3600 | not rerun |
| Semantic Logistic | 0.5888 | — | 0.0332 | 0.4225 | 0.6688 |
| Semantic MLP | 0.6042 | 0.0050 | 0.0385 | 0.4210 | **0.6790** |
| Semantic Shared | 0.5990 | 0.0035 | 0.0370 | 0.4040 | 0.6653 |
| Hybrid lexical+semantic | 0.6034 | — | 0.0304 | 0.3025 | 0.6744 |
| Confidence fallback | 0.6095 | — | 0.0575 | **0.4275** | 0.6800 |
| Disagreement fallback | 0.6049 | — | 0.0465 | 0.4050 | 0.6714 |
| Oracle | 0.7896 | — | 0.0145* | 0.5350 | 0.8749 |

`*` Oracle cost is descriptive only: it optimizes quality, and ties can select cheap models.

Paired query bootstrap differences against Best Single were +0.0048 [−0.0082, 0.0181] for the
mean semantic MLP seed, −0.0004 [−0.0139, 0.0134] for Shared, +0.0040 [−0.0116, 0.0196] for Hybrid,
and +0.0101 [0.0040, 0.0166] for the validation-frozen confidence fallback. These repeated-test
intervals quantify sampling uncertainty, not independent confirmation and not multiplicity-adjusted
significance.

## Research questions

- **RQ1:** unsupported on proprietary-8. Frozen semantics did not beat TF-IDF ID. MLP was close and
  generalized far better to ARC, but still did not beat Best Single there.
- **RQ2:** mixed. Leave-dataset-out Semantic Logistic beat Best Single on ArenaHard, creative
  writing, and coding, but lost on SimpleQA (0.400 vs 0.537), HLE (0.165 vs 0.215), MMLU-Pro
  (0.847 vs 0.859), and most other folds. The macro evidence does not support universal gains.
- **RQ3:** confidence fallback reduced ID risk (28.2% of choices changed) but on ARC selected Best
  Single sufficiently often to equal, not exceed, it. Disagreement fallback was weaker.
- **RQ4:** the revised primal-dual gate corrected the old cheap-model collapse. At matched budget
  fractions 25/50/75/100%, its ID quality was 0.5778/0.5873/0.6029/0.6130 with no realized budget
  violation, versus 0.5732/0.5873/0.5888/0.5888 for the validation-selected deterministic policy.
  This promising upper-budget result is exploratory and needs independent replication.
- **RQ5:** findings partly replicate. On lightweight-20 MLP (0.6790) and confidence fallback
  (0.6800) slightly exceed the historical TF-IDF estimate (0.6778), while Shared and Logistic do
  not. Lightweight historical monetary cost excludes hardware and is not cost-comparable.

## Calibration and compute

On ID, MLP Brier/log-loss/ECE were 0.2069/0.6029/0.0262. On ARC they deteriorated to
0.2144/0.6199/0.2486. Semantic representation improved OOD routing relative to TF-IDF without
producing transferable probability calibration. MiniLM extraction encoded 26,367 queries in
460.2 s (57.3 q/s), producing a 37 MB cache. Full online encoding measured 10.35 ms/query singly
and 2.13 ms/query at batch 128 (four CPU threads); loading added about 29 MB RSS in that process.
Heads contained 3,080 (logistic), 25,160 (MLP), and 18,849 (Shared) fitted parameters and trained in
0.2, 0.7, and 0.8 seconds respectively. Encoder cost dominates.

## Final recommendation

**CONTINUE ROUTING RESEARCH.** Do not move to hardware-aware Phase 4 yet. The revised gate and
confidence fallback are credible candidates for a preregistered independent evaluation, but no
semantic method establishes a robust advantage over both TF-IDF ID and Best Single OOD. RouterBench
is a plausible public confirmatory source, yet it overlaps this project's upstream benchmark
families and its exact model pool differs; it cannot be called independent without a documented
overlap audit and a newly frozen protocol.
