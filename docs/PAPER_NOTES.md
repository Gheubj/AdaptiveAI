# Paper Notes

## Working title

Hardware-Aware, Quality-Constrained Routing for Hybrid LLM Inference

## Proposed structure

1. Motivation and research questions
2. Related work in LLM routing and cost-aware inference
3. Data provenance and benchmark construction
4. Quality-only and rule-based baselines
5. Neural quality router
6. Hardware-aware objective and switching costs
7. Experimental protocol, ablations, and statistical analysis
8. Threats, ethical considerations, and reproducibility

## Claims discipline

Do not claim novelty or superiority until preregistered comparisons, uncertainty estimates, and
ablation studies support them. Distinguish dataset observations from causal hardware conclusions.

## Phase 1B evidence to retain

- Strong matched coverage supports controlled routing research, especially lightweight-20.
- Repeated upstream subsets and non-random missingness require explicit protocol rules.
- Current data support quality/historical-cost routing, not hardware-aware conclusions.
- Report benchmark-level paired comparisons; avoid an unqualified global leaderboard.
# Phase 2 draft material

**Datasets.** We use the content-addressed current LLMRouterBench archive and distinguish it from the
paper-era 391,645-instance dataset. Experiments use grouped custom splits and complete 20-model or
8-model panels; repeated releases are aggregated by cell.

**Experimental setup.** Routers train on train, budget policies are selected on validation, and test
is used once. The primary metric is task success; per-dataset and upstream-score summaries accompany
macro/micro results. Oracle is post-hoc.

**Preliminary results.** TF-IDF improves ID test success by 2.31 points on lightweight and 1.61 on
proprietary, but not proprietary validation and not ARC-AGI OOD. This motivates a robustness-focused
neural study, not a conclusion of general superiority.

**Limitations.** Paper subset mismatch, benchmark-source shortcuts, MNAR scores, incomplete panels,
historical price confounding, proprietary drift, and missing hardware measurements remain.

## Phase 3 draft material

We compare a sparse EmbeddingBag predictor, a query/model embedding interaction model, and a learned
quality-cost gate under equal CPU budgets. The sparse model is competitive with TF-IDF ID but does
not exceed it. Explicit model embeddings hurt, while sparse features partially reduce the ARC-AGI
failure without beating Best Single. Learned gating collapses toward cheap routes and underperforms
direct constrained selection. These negative results motivate a new confirmatory holdout and stronger
semantic/OOD data, not a hardware-aware performance claim.

## Phase 3.5 framing

Provisional contribution: a controlled negative/qualified study of lexical, sparse, and frozen
semantic routing under dataset shift, plus matched-budget diagnosis of constrained gating. Standard
encoders, MLPs, and Lagrangian optimization are baselines, not methodological inventions. Avoid
hardware-aware, universal-generalization, or independent-validation claims.

## Consolidated narrative after freeze

Provisional title: *Learning to Route Language Models: Quality, Cost, and Generalization Under
Distribution Shift*. Lead with the grouped real-evaluation protocol and strong lexical baseline;
present sparse/semantic routing as qualified robustness evidence, shared embeddings and original
gating as negative results, and matched-budget gating as a control lesson. State prominently that
no exact-panel independent confirmation was available. Hardware work is a separate systems study.

## Hardware-Aware LLM Routing section

Present the pinned local backend, registry, cold/warm protocol, objective local panel, constrained
selector, and end-to-end execution separately from offline routing. Report that fixed-fastest
dominates on the micro-panel. Loading and RAM are real constraints; neural, energy, and cloud
advantages are not supported.
# Phase 4.5 manuscript update

Local setup: AMD Ryzen 5 PRO 6650U, six CPU inference threads, 14.4 GiB RAM, llama.cpp `a300a9c`,
Qwen2.5-0.5B and SmolLM2-1.7B Q4_K_M. A frozen 500-query matched panel and typed scorer replace the
Phase 4 micro-panel for new claims. Held-out accuracies are .172 [.128,.220] and .416 [.356,.480].
The paired difference [.188,.300] supports SmolLM2 on this workload. Complementarity counts
41/2/63/144 imply oracle .424 and only .008 headroom above SmolLM2. Hardware-aware, TF-IDF, and
semantic policies do not exceed Fixed Strongest. Real switching, not router compute, dominates the
task-aware latency path. Engineering novelty is reproducible constrained local orchestration and
failure recovery; scientific evidence does not establish hardware-aware superiority or validate
the earlier proprietary-8 results.

# Phase 5 engineering note

The product contribution is a local-first observable routing interface with validated constraints,
lifecycle-aware selection, streaming, error handling, and reproducible packaging. It adds no new
quality result and does not change Phase 4.5 conclusions. Separate engineering contribution from
scientific novelty and avoid production-readiness claims.
