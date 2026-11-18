# Results Registry

## Phase 1B descriptive results — 2026-11-18

- Source SHA-256: `b79f8cde...648c8f1`.
- 548,046 accepted evaluations, 26,367 queries, 40 models, 27 datasets.
- 26,366 queries have >=5 model results; median 20 models/query.
- 13 quarantined records (0.002372%); 4,327 missing scores (0.7895%).
- Zero duplicate-group leakage across custom splits.

These are descriptive data-validation results, not evidence of router superiority. Preliminary
baseline artifacts are diagnostic and remain separated by benchmark. Synthetic fixture outcomes
are excluded.
# Phase 2 registered artifacts

- `reports/phase2/runs/lightweight20-test-dcaadcccf15a`: final lightweight ID test.
- `reports/phase2/runs/proprietary8-test-c0bdfbfd3c59`: final proprietary ID test.
- `reports/phase2/runs/proprietary8-validation-8db20881e516`: validation budget selection.
- `reports/phase2/runs/proprietary8-ood_test-fcdc242fc2b9`: ARC-AGI OOD.
- `reports/phase2/sensitivity`: representative/exclude resolution policies.
- `reports/phase2/budget_frontier.parquet`: validation-selected budget grid with untouched test values.
- `reports/phase2/statistical_summary.json`: paired intervals and random-seed dispersion.

All are preliminary Phase 2 results, not final paper conclusions.

# Phase 3 artifacts

- `reports/phase3/proprietary8-main`: five-seed checkpoints, decisions, calibration and resources.
- `reports/phase3/ablations/ablation_results.parquet`: validation-only studies.
- `reports/phase3/cross_dataset/train_only_leave_dataset_out.parquet`: transfer folds.
- `reports/phase3/paired_comparisons.parquet`: paired ID/OOD intervals versus TF-IDF.
- `reports/phase3/calibration_summary.parquet`, `reliability_diagrams.png`.
- `reports/phase3/latency_summary.parquet`, `gate_resources.parquet`.

All holdout results are exploratory because Phase 2 previously exposed test and ARC-AGI.

## Phase 3.5 (`reports/phase3_5`)

- Proprietary ID: Semantic Logistic 0.5888; MLP 0.6042 ± 0.0050; Shared 0.5990 ± 0.0035;
  Hybrid 0.6034; confidence fallback 0.6095.
- ARC-AGI: Logistic 0.4225; MLP 0.4210 ± 0.0091; Shared 0.4040; confidence fallback 0.4275.
- Lightweight ID: Logistic 0.6688; MLP 0.6790 ± 0.0019; Shared 0.6653; Hybrid 0.6744.
- Revised gate at 25/50/75/100% budgets: 0.5778/0.5873/0.6029/0.6130, zero test violations.
- Status: exploratory repeated evaluation; recommendation **CONTINUE ROUTING RESEARCH**.

## Phase 3.6 (`reports/phase3_6`)

- Confirmatory evaluation: not conducted; no eligible independent exact-panel benchmark.
- Revised gate minus deterministic selector: +.0045, .0000, +.0141, +.0242 at four budgets;
  upper two paired intervals exclude zero on the repeated test.
- Constrained TF-IDF quality/cost at 75/100%: .6155/.03906; revised gate .6029/.03975 and
  .6130/.04783.
- CPU p50/p95 ms: TF-IDF 1.51/1.81; Sparse A .39/.64; Semantic MLP 25.86/29.29; revised gate
  30.00/39.20.
- Decision: **GO TO PHASE 4 WITH VALIDATION LIMITATIONS**.

## Phase 4 (`reports/phase4`)

- Qwen: load p50 .528 s, warm-long TTFT p50 .036 s, total p95 .651 s, peak RSS .532 GB.
- SmolLM2: load p50 1.704 s, warm-long TTFT p50 .062 s, total p95 1.694 s, peak RSS 2.288 GB.
- Strict test quality: .25 both (8 queries); post-hoc relaxed: .875 Qwen, .750 SmolLM2.
- Every policy scored .25 strict; fixed-fastest latency .321 s vs hardware-aware .754 s.
- Energy N/A; zero failures. Decision: **CONTINUE HARDWARE RESEARCH**.
# Phase 4.5 registered results

- `reports/phase4_5/benchmark_v2_frozen.parquet`: 500 frozen prompts, 150/100/250 splits.
- `scorer_validation.parquet`: 14/14 expected scorer decisions.
- `matched_model_outputs.parquet`: 1,000 matched local responses.
- `model_summary.parquet`: held-out model quality, intervals, latency, RAM, failures.
- `policy_decisions.parquet` / `policy_summary.parquet`: 2,500 policy decisions and summaries.
- `paired_comparisons.parquet`: paired bootstrap and exact McNemar comparisons.
- `end_to_end_policy_execution.parquet`: 96 real lifecycle-aware policy requests.
- `analysis_metadata.json`: frozen selections and complementarity statistics.

# Phase 5 verification artifacts

- `dist/adaptiveai-0.1.0-py3-none-any.whl`: code-only experimental wheel.
- `dist/adaptiveai-0.1.0.tar.gz`: sdist excluding research data/weights/vendor/reports.
- `docs/PHASE5_REPORT.md`: implementation and real smoke-test record.
- `docs/OPEN_SOURCE_AUDIT.md`: large-file, secret, license, history, and packaging audit.
- `docs/RELEASE_CHECKLIST.md`: completed items and owner-controlled blockers.
