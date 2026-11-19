# Project State

Updated: 2026-11-18 (Phase 6A working branch)

## Current status

Phase 6B.5 is implemented locally on top of Phase 6B commit `6af2021`. Audits found xRouteBench
technically fit for matched prompt/model routing supervision and RoutingCompendium useful for
cross-pool study, but neither currently has a sufficiently explicit row-level permission basis for
ingestion: xRouteBench declares no dataset license, while RoutingCompendium delegates rights to five
source benchmarks without a consolidated matrix. No external rows were downloaded. Source-neutral
schemas, fixture adapter, matrix/leakage/complementarity/cost analysis, and Phase 6C preregistration
were implemented offline. Decision: **BLOCKED BY DATA RIGHTS / DATA QUALITY** pending clarification.
Final verification passed with 98 tests, three expected skips, 68% whole-package coverage, 91–100%
new-module coverage, clean Ruff/format, successful builds and clean-target imports. Focused tests
used 48,548 KiB peak RSS; no external dataset bytes were ingested.

Phase 6B is implemented locally on top of Phase 6A commit `6bedc34`. One bounded anonymous import
used the official Hugging Face leaderboard API for SWE-bench Verified: 59,880 bytes, 78 source rows,
20 accepted under the configured limit, zero malformed rows, 20 unresolved identities, 20 unknown
revisions, and zero independently verified records. Raw/normalized records remain in ignored local
storage because redistribution permission is unknown. No routing claim, paid API, inference, model
download, push, tag, or release was made. Final verification passed with 90 tests, three expected
opt-in skips, 65% whole-package coverage, clean Ruff/format, successful package builds, clean archive
inspection, and clean-target CLI/module imports.

Phase 6A is implemented on the unpublished `codex/phase6a` branch as an additive model-intelligence
foundation. It adds exact identity and revision semantics, typed evidence/provenance, permission
gates, comparability diagnostics, versioned capability profiles, deterministic eligibility, a
fixture-backed benchmark adapter, and a v0.1.0 compatibility adapter. It used no real external
source, paid API, model download, training, or benchmark run. Phase 6B remains proposal-only and no
release action is authorized. Final verification passed with 82 tests, two optional integration
skips, clean Ruff/format checks, 60% whole-package coverage, and clean wheel/sdist inspection.

Phase 2 is complete for reproducible routing baselines on the frozen Phase 1B data. The official
LLMRouterBench archive is stored outside Git with SHA-256
`b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`. All 700 JSON files were
audited; 548,046 evaluations were normalized from 548,059 records, with 13 invalid negative-token
records quarantined.

The normalized dataset contains 26,367 queries, 40 source model IDs, and 27 datasets. Referential,
schema, numeric, reproducibility, and grouped leakage checks pass. 26,366 queries have at least five
model results. A real 470-model OpenRouter snapshot is stored separately from historical benchmark
prices; all 40 cross-source model identities remain unresolved under exact-only matching.

Real EDA, coverage/intersection tables, missingness/conflict reports, preliminary train-selected
baselines, license audit, and Phase 1B documentation are available. No paid API or model generation
was used.

## Known limitations

- Phase 6B.5 contains no new external matched outcomes; public dataset-card counts are audit metadata,
  not locally validated empirical results.
- Exact/near-duplicate leakage beyond normalized text hashes requires a permission-cleared snapshot.
- Historical routing identities cannot be promoted to live deployments without revision mapping and
  targeted current calibration.

- Phase 6B evidence describes agent/model systems, not isolated base-model quality; exact revisions
  and scaffolds are unknown for every pilot row.
- All accepted live rows were source-declared (`verified=false`) and redistribution remains denied.
- The bounded 20-row pilot is deliberately incomplete and cannot support universal ranking or
  prompt-aware routing validation.

- Phase 6A contains no admitted real provider or benchmark source; its adapter is fixture-only.
- Provider aliases, availability, pricing, and capabilities are time-varying and require explicit
  source-specific freshness policy in a later phase.
- The eligibility layer is a deterministic safety gate, not a quality rank or inference guarantee.

- 10,881 repeated query/model pairs arise from overlapping upstream releases; 237 scores conflict.
- 4,327 scores are missing non-randomly, primarily one SimpleQA/model panel.
- Constituent dataset redistribution rights are not fully resolved.
- Most questions originate from upstream evaluation splits.
- Historical zero monetary cost for local models excludes hardware cost.
- Aggregate `time_taken` is not request latency; hardware measurements are absent.
- Exact OpenRouter identity mapping is unresolved for every benchmark model name.

## Verification

- Full archive integrity/safety scan: passed.
- Dataset validation: passed with zero duplicate-group split leakage.
- Final verification: 25 offline tests passed (77% coverage), the optional real-archive integration
  test passed locally, Ruff passed, and normalized validation passed.
- Phase 2 final verification: 35 offline tests passed, one optional real-data test skipped without
  its environment variable, 75% phase-scoped statement coverage, Ruff clean, and normalized
  validation clean.
- Phase 3 final verification: 39 offline tests passed, one optional real-data test skipped, 67%
  statement coverage across the expanded training/experiment code, Ruff clean, normalized validation
  clean, seven required artifact groups present, and 15 neural checkpoints present.
- Normalization: 175.34 s, 1.34 GB peak RSS.
- Duplicate grouping: 53.78 s, 410 MB peak RSS for 26,367 queries.
- EDA: 14.10 s, 847 MB peak RSS.

## Phase 3 status and next tasks

All three required PyTorch architectures, five-seed real-data experiments, calibration, ID/OOD,
train-only cross-dataset diagnostics, ablations, and resource measurements are complete. Sparse A
reaches 0.6086 ID versus TF-IDF 0.6155 and 0.3600 ARC-AGI versus TF-IDF 0.2525, but remains below
Best Single OOD. Shared B is weaker; Gate C is worse than deterministic constrained selection.

1. Reserve and preregister a new confirmatory holdout.
2. Evaluate a small licensed semantic encoder under the same budget.
3. Redesign constrained learning and retain the deterministic selector control.
4. Collect hardware data only after quality/OOD entry criteria pass.

Phase 2 ID test: TF-IDF 0.6778 vs Best Single 0.6547 (lightweight) and 0.6155 vs 0.5994
(proprietary). Paired 95% intervals for the differences exclude zero, but proprietary validation
does not and ARC-AGI OOD strongly reverses the result (0.2525 vs 0.4275). Decision: **GO TO PHASE 3**
for controlled robustness-focused research. Hardware-aware claims remain blocked.

Phase 3 decision: **NOT READY FOR PHASE 4**.

## Phase 3.5 status

Phase 3.5 is complete. Frozen MiniLM semantic Logistic, MLP, Shared, and Hybrid routers; train-only
cross-dataset folds; confidence/disagreement fallbacks; revised primal-dual gating; matched budgets;
and lightweight-20 replication were evaluated. Semantic MLP reached 0.6042 ± 0.0050 proprietary ID
and 0.4210 ± 0.0091 ARC-AGI, versus TF-IDF 0.6155/0.2525 and Best Single 0.5994/0.4275. The revised
gate corrected the old collapse and reached 0.6130 at the full matched budget, but all test/ARC
results are repeated exploratory evaluations. Final recommendation: **CONTINUE ROUTING RESEARCH**;
Phase 4 remains blocked pending independent confirmation.

Phase 3.5 verification: 44 offline tests passed, one optional integration test skipped, Ruff clean,
dataset validation clean, and 58% statement coverage. The decrease reflects end-to-end experimental
orchestration code; core semantic/fallback/budget primitives have focused tests.

## Phase 3.6 status

Routing research is frozen. A preregistered audit found no independent public benchmark with the
same exact eight-model panel; no confirmatory claim was made. The matched-budget rerun shows revised
gating beats its deterministic semantic control at 75/100% budgets, but constrained TF-IDF remains
stronger and cheaper. Standard CPU router benchmarks and a hardware execution plan are complete.
Decision: **GO TO PHASE 4 WITH VALIDATION LIMITATIONS**. Phase 4 was not implemented.

Phase 3.6 verification: 47 offline tests passed, one optional integration test skipped, Ruff clean,
dataset validation clean, JSON/artifact checks passed, and gating aggregates reproduced Phase 3.5
exactly. Total statement coverage is 55% after adding two end-to-end runners; semantic core coverage
rose to 66%, while orchestration remains the principal untested surface.

## Phase 4 status

Phase 4 is complete as a research prototype. Hardware discovery, pinned llama.cpp inference, two
real local Q4 models, cold/warm/streaming/concurrency measurements, a frozen 24-query objective
panel, constrained policies, real routed execution, CLI, localhost API, and mock cloud abstraction
are implemented. Fixed Qwen matches SmolLM2 strict test quality (.25) with lower latency and RAM;
hardware-aware selection adds no observed gain. Energy is N/A. Decision: **CONTINUE HARDWARE
RESEARCH** before a Phase 5 Product MVP.

## Phase 4.5 status

Phase 4.5 is complete. A preregistered 500-query V2 panel (150/100/250), six task families, frozen
task-aware scorer, 1,000 real matched generations, complementarity/oracle analysis, ten policies,
MiniLM semantic control, paired uncertainty, and 96 real policy-execution requests were completed.
SmolLM2 scores .416 test accuracy versus Qwen .172; the paired difference is .244, 95% bootstrap
CI [.188,.300]. However oracle gains only .008 over SmolLM2, and no learned policy beats Fixed
Strongest. Task-aware routing matches quality offline but model switching destroys its latency
advantage in real execution. Decision: **GO TO PHASE 5 WITH RESEARCH LIMITATIONS** for an explicitly
experimental local open-source MVP, without a hardware-routing superiority claim.

Phase 4.5 verification: 65 tests passed and one optional integration test skipped; Ruff, formatting,
dataset validation, JSONL parsing, and diff checks passed. Total statement coverage is 78%.

## Phase 5 status

Phase 5 is complete as an experimental 0.1.0 release candidate. It adds validated TOML, public
interfaces, four routing modes, explicit selection, lifecycle hysteresis/cleanup, dynamic local
ports, bounded API/SSE, client, product CLI, examples, optional research dependencies, CI, release
artifacts, and documentation. Real local CLI/API smoke-tests passed. Restricted data, weights,
caches, vendor sources, and reports are excluded from release artifacts. The candidate is **READY
FOR OWNER APPROVAL**; publication remains prohibited pending owner approval of the license,
attributions/notices, exact staged manifest, and destination. Phase 6 was not started.

Release-gate verification: 75 tests passed, one optional archive integration skipped, 57%
whole-package statement coverage, real local CLI/API streaming smoke passed, isolated wheel
`pip check` passed, and release archives contain no raw datasets, weights, processed caches, vendor
tree, or reports. The earlier 75% figure was phase-scoped.
# Phase 6G development status (2026-11-19)

Phase 6G implements an opt-in, provider-independent BYOK gateway on branch `codex/phase6g`.
The OpenAI-compatible adapter, endpoint validation, provider scopes, streaming, typed errors,
usage/cost records, strict budgets, CLI/SDK surfaces, and offline mock integration are implemented.
No real cloud inference, paid request, model download, or research dataset download was performed.
Quality for newly configured cloud models remains unknown; no routing superiority or saving is
claimed. Phase 6B.5 remains frozen in local commit `5d7e650`.

# Phase 7 Developer Alpha status (2026-11-19)

Phase 6G is preserved in local commit `40af4a1`. Phase 7 adds a real localhost provider E2E path,
explainable deterministic Auto V0, Economy/Manual modes, task-understanding abstention,
eligibility-first selection, strict comparable-evidence rules, dry-run explanations, atomic budget
reservations and a zero-cost cloud-only quick start. Examples use explicitly synthetic evidence.
External providers remain unvalidated and no routing superiority claim is made.

# Phase 7.1 status (2026-11-19)

Phase 7 is preserved in local commit `a13e808`. Phase 7.1 prepares an exact, zero-price OpenRouter
candidate with one pinned upstream, provider fallback disabled, and a non-network fail-closed smoke
preflight. No external inference was authorized or executed; spend is USD 0. Status is
`READY_FOR_OWNER_AUTHORIZATION`. Current version remains 0.1.0; v0.2.0a1 is only a developer-preview
proposal. Phase 8 was not started.
