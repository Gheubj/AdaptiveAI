# Research Log

## 2026-11-17 — Phase 1 foundation

- Inspected the official GitHub documentation, Hugging Face file listing, evaluator documentation,
  and OpenRouter model API reference.
- Confirmed that the official Hugging Face repository exposes `bench-release.tar.gz` (listed as
  1.28 GB) rather than viewer-ready Parquet tables.
- Implemented source-preserving ingestion, validation, normalization, catalog snapshots, splits,
  EDA, tests, and research-run logging.
- Did not download the large archive and did not call any paid model endpoint.
- No empirical routing result was produced. This is a software verification session, not a model
  comparison experiment.
- Verification completed with 15 passing offline tests, 64% statement coverage, and a clean Ruff
  check. The explicit downloader is tested through an in-memory HTTP transport, not the network.

## 2026-11-17/18 — Phase 1B real-data integration

- Verified 58 GB free disk, then acquired the 1.283 GB official archive. A CDN interruption after
  ~64 MB motivated persistent Range resume and retry support.
- Verified SHA-256 `b79f8cde...648c8f1`; scanned 700 safe JSON members and 548,059 records.
- Fixed two undocumented real archive path layouts and live OpenRouter structured pricing fields.
- Normalized 548,046 evaluations; quarantined 13 negative-completion-token records.
- Measured coverage, repeated-run conflicts, missingness, duplicates, leakage, and two matched pools.
- Generated real EDA and train-selected preliminary baseline artifacts. No paid inference occurred.

## 2026-11-18 — Phase 2 routing baselines

- Reconciled the current 548,046-row archive with the paper's 391,645-instance claim. The published
  21-dataset/33-model whitelist selects 431,776 current rows, so exact paper reproduction remains
  impossible without a paper-era file manifest.
- Classified 10,881 repeated pairs (237 conflicting); froze mean-cell resolution with representative
  and exclusion sensitivity analyses.
- Implemented Random, Cheapest, train-selected Best Single, metadata-assisted Task-Aware, per-model
  TF-IDF logistic, cost-constrained, and post-hoc Oracle methods under one engine.
- Completed ID test runs, proprietary validation budget selection, proprietary ARC-AGI OOD, five
  random seeds, bootstrap uncertainty, Pareto artifacts, plots, and failure analysis.
- Fixed two performance defects discovered during real runs: accidental raw-output loading and
  per-query TF-IDF transforms. Final runs use batch inference and peak at 1.17 GB RSS.

## 2026-11-18 — Phase 3 neural routing

- Installed CPU-only PyTorch 2.15; no pretrained model or paid inference was used.
- Implemented Sparse A, Shared Query/Model B, Trainable Gate C, and the required deterministic
  constrained control on the same B predictions.
- Completed five-seed real proprietary-8 runs, calibration, ID/OOD evaluation, BCE/MSE and dimension
  ablations, three train-only held-dataset folds, paired bootstrap, and CPU resource measurements.
- No neural method beats TF-IDF ID. A improves on TF-IDF ARC-AGI but not Best Single; B adds no
  stable benefit; C collapses toward cheap routing and loses to its deterministic control.
- Phase 4 implementation was not started.

## 2026-11-18 — Phase 3.5 semantic and robust routing

- Revision-pinned frozen MiniLM encoded 26,367 queries on CPU in 460.2 seconds; no paid API used.
- Evaluated Semantic Logistic, MLP, Shared, Hybrid, two fallbacks, train-only held-dataset folds,
  revised constrained gating at four matched budgets, and lightweight-20 replication.
- Semantic MLP approached but did not beat TF-IDF proprietary ID; it nearly matched Best Single ARC.
- Confidence fallback improved repeated ID evaluation but only matched Best Single ARC. ARC
  calibration remained poor.
- Revised gating removed the historical cheap-model collapse and respected all tested budgets.
- Independent confirmation was assessed but not claimed. Phase 4 remains blocked.

## 2026-11-18 — Phase 3.6 research freeze

- Preregistered frozen candidates, endpoints, exclusions, and success criteria before external-label
  discovery.
- Audited LLMRouterBench, RouterBench, RouterEval, RouteLLM, and RouterArena. No independent source
  has the exact complete proprietary-8 panel; confirmatory evaluation was skipped honestly.
- Reproduced revised gating at four budgets and persisted query decisions. It beats the semantic
  deterministic control at upper budgets but not constrained TF-IDF.
- Benchmarked TF-IDF, Sparse A, Semantic MLP, and revised gate on the same CPU protocol.
- Froze routing development and prepared Phase 4 measurements without downloading LLM weights.

## 2026-11-18 — Phase 4 local hardware routing

- Built llama.cpp `a300a9c` CPU-native; downloaded two Apache-2.0 Q4_K_M models totaling 1.453 GB
  and verified hashes.
- Executed 66 profile observations, 48 matched quality requests, 24 concurrency requests, and four
  additional real routed requests on localhost.
- Qwen was faster and used .532 GB versus SmolLM2 2.288 GB. Both scored .25 strict test quality.
- Hardware-aware routing chose validation-stronger SmolLM2 but gained no test quality and was slower;
  neural policy was skipped because the panel is too small.
- Energy is N/A because readable hardware counters were unavailable.

## 2026-11-18 — Phase 4.5 expanded local validation

- Froze a new 500-query, six-family objective panel and 14-case scorer validation suite before model
  evaluation; the original Phase 4 test was not reused as confirmatory evidence.
- Executed 1,000 matched local model requests with resumable row-level persistence. A localhost
  timeout at row 133 exposed an uncaught error path; timeout translation, restart, and tests were
  added, then execution resumed without recomputing 132 preserved rows.
- SmolLM2 reached .416 held-out accuracy versus Qwen .172. Both/only-Qwen/only-Smol/neither counts
  were 41/2/63/144; oracle .424 leaves only .008 headroom over SmolLM2.
- TF-IDF, frozen MiniLM semantic, and hardware-aware policies all selected the validation-stronger
  model and did not beat it. Task-Aware matched its quality offline.
- Ran 96 additional real policy requests. Sixteen task-aware switches consumed 24.79 seconds of
  loading and increased p95 end-to-end latency to 3.53 seconds.
- No additional model, paid API, unsafe code execution, or cloud compute was used.

## 2026-11-18 — Phase 5 experimental MVP

- Separated core product modules from optional research dependencies and prepared 0.1.0 packaging.
- Added configuration, public types, routing modes, explicit choice, lifecycle hysteresis, bounded
  API/SSE, client, onboarding CLI, examples, and CI.
- Real smoke-tests exposed a fixed-port collision; internal servers now use dynamic loopback ports.
  Non-streaming and streaming CLI/API requests then passed with process cleanup.
- Initial sdist inspection caught a MiniLM cache; explicit exclusions were added and the rebuilt
  artifacts contain no raw/models/processed/vendor/reports directories.
- Audited secrets, large files, dependencies, licenses, and publication controls. Nothing was
  published and no Phase 6 work began.
