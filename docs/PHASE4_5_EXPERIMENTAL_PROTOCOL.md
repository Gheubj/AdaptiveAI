# Phase 4.5 Experimental Protocol (Frozen)

Frozen on 2026-11-18 before any Phase 4.5 model output or held-out label was inspected.

## Research questions and hypotheses

The primary question is whether query-dependent routing between the two already registered local
models improves objective answer accuracy over Fixed Fastest at an acceptable latency and memory
cost. Secondary questions concern model complementarity, oracle headroom, prediction error,
switching overhead, and constraint violations. H1 is that at least one deployable router has a
positive paired accuracy difference over Fixed Fastest. H2 is that hardware-aware selection lies on
the measured quality/latency Pareto frontier. H3 is that oracle gain over Best Single is positive.
Failure to reject a null is not evidence of equivalence.

## Frozen model pool and runtime

The confirmatory pool is Qwen2.5-0.5B-Instruct Q4_K_M and SmolLM2-1.7B-Instruct Q4_K_M from the
existing hash-pinned registry. llama.cpp commit `a300a9c33462f23d9d61e951650d249486f2b0f6`, CPU/OpenMP,
six threads, context 2,048, temperature zero, seed 3407, and the model's own GGUF chat template are
fixed. No additional weights may be selected after test inspection.

## Benchmark V2

The benchmark contains 500 unique, locally generated Apache-2.0 objective tasks: 150 train, 100
validation, and 250 test. Split sizes are fixed now. Six stratified families are arithmetic,
closed factual QA, structured extraction, exact instruction following, simple programming/output
tracing, and deterministic reasoning. Each row retains a query ID, generator version, task family,
reference, schema/answer type, and generation seed. Generation uses only frozen fact tables and
deterministic templates; no Phase 4 prompt is reused verbatim. The original eight-query Phase 4
test is exploratory and is not pooled into V2.

The locally authored benchmark is reproducible and redistribution-safe, but its templated nature
limits ecological and contamination claims. Exact normalized prompt duplicates across splits are
excluded. The test size will not change after test results are observed.

## Scoring

Primary quality is task-aware binary correctness. Numerical answers use a frozen final-answer
extractor, decimal equivalence, and tolerance `max(1e-6, 1e-6*abs(reference))`. Factual answers use
case/Unicode/punctuation normalization and frozen aliases. Extraction parses the requested schema
and compares every field. Instruction tasks compare the required normalized serialization.
Programming tasks ask for deterministic output or expression values and are scored as numeric or
exact text; generated code is never executed. Reasoning uses typed numeric, boolean, or exact-text
references. Ambiguous parses are recorded as `unscorable`, never silently correct.

Before model evaluation the scorer must pass a manually specified development suite containing
valid paraphrases, extra-prose cases, ambiguity, and adversarial distractor numbers. Expected false
positives and false negatives on this suite are both zero. The Phase 4 strict scorer and results
remain unchanged.

## Metrics and statistical procedures

For each model and policy report accuracy with query-cluster bootstrap 95% intervals, per-task
accuracy, both/only-A/only-B/neither counts, disagreement, correctness phi correlation, oracle
accuracy, and oracle gains. Paired accuracy comparisons use paired query bootstrap and McNemar's
exact binomial test. Latency reports p50/p95, paired differences with query bootstrap intervals,
TTFT, generation rate, load time, switch cost, peak child RSS, failures, timeouts, and realized
constraint violations. Repeated hardware runs quantify measurement variability and never increase
the query sample size.

## Routing policies

Frozen candidates are Fixed Fastest, validation-selected Fixed Strongest, seeded Random,
validation-selected Task-Aware, locally trained per-model TF-IDF success predictors, Semantic only
if the frozen local embedding cache is available without new model selection, Latency-Aware,
Memory-Aware, Hardware-Aware, and post-hoc Oracle. All deployable policies use prompt/pre-inference
features only. Local quality predictors fit train labels; thresholds and hyperparameters use
validation only. Test labels, observed generation length, and observed latency cannot be features.

For eligible set `E(x,h)`, hardware-aware routing maximizes predicted correctness, breaking ties by
predicted latency, subject to local-only, availability, RAM, loaded-state-adjusted p95 latency, and
cost constraints. Realized violations compare actual latency/RSS against the same declared budget.

## Exclusions and failures

Exclude only preregistered malformed benchmark rows, registry hash mismatch, or backend responses
with explicit timeout/crash status; failures remain in denominators with correctness zero. No row is
excluded for a wrong or verbose answer. Missing paired outputs block the paired comparison and are
reported. Test queries may not tune prompts, scoring, models, policies, thresholds, or sample size.

## Success criteria

Scientific success requires positive oracle headroom and a deployable policy whose paired accuracy
improvement over Fixed Fastest has a 95% interval excluding zero, or a policy on a strictly better
measured Pareto point under a prespecified constraint. Engineering success requires reproducible
artifacts, real backend execution, zero silent failures, critical-path tests, and documented
limitations. Public experimental-MVP readiness does not require universal superiority, but does
require safe local defaults, reproducible installation, explicit errors, and honest scientific
labelling.
