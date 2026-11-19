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

## 2026-11-18 — Phase 6A model intelligence foundation

- Implemented strict provider-independent identities for families, exact/unknown revisions,
  quantization, providers, time-bounded aliases, deployments, and evaluation configurations.
- Added content-addressed evidence with explicit missingness, provenance, reliability, permission
  metadata, duplicate rejection, and structured comparability diagnostics.
- Added deny-by-default redistribution decisions, versioned tri-state capability profiles, and
  deterministic eligible/ineligible/unknown deployment checks with stable reason codes.
- Added a synthetic fixture-only benchmark adapter and a compatibility wrapper that delegates to
  the unchanged v0.1.0 routing engine.
- Performed no real-source ingestion, model inference, training, network pilot, paid API call, or
  model download. Phase 6B is documented only as a gated proposal.

## 2026-11-18 — Phase 6B external evidence pilot

- Audited the official Hugging Face dataset leaderboard API and SWE-bench Verified semantics.
- Made two bounded anonymous metadata requests totaling 119,760 bytes: schema inspection and the
  adapter pilot. No task data, outputs, trajectories, or weights were downloaded.
- The pilot accepted 20 of 78 advertised rows, preserving original percent scores and complete
  provenance. All 20 revisions and identities remain unresolved and all rows were unverified.
- Stored the immutable snapshot and evidence SQLite database outside Git; permission-aware public
  export denies every record because result redistribution is not explicitly licensed.
- Added mocked/offline tests, opt-in live integration, conservative comparison/profile queries, and
  CLI/example workflows. Phase 6C was not started.

## 2026-11-19 — Phase 6B.5 routing data fitness

- Preserved Phase 6B as local commit `6af2021` before new work.
- Audited xRouteBench and RoutingCompendium without downloading row-level data. xRouteBench has the
  stronger supervision schema but no declared dataset license; RoutingCompendium inherits multiple
  unresolved source licenses.
- Added distinct routing-supervision records, bounded adapter contracts, explicit missing matrix
  cells, duplicate/conflict checks, deterministic sampling, leakage checks, binary Oracle and
  pairwise analysis, historical-cost refusal, and baseline eligibility.
- Used only synthetic fixtures for calculations. No neural router, external dataset, paid API,
  inference, model weights, or cloud integration was used. Phase 6C was preregistered only.
# 2026-11-19 — Phase 6G

- Preserved Phase 6B.5 as local commit `5d7e650` and created `codex/phase6g`.
- Added an offline-tested BYOK cloud gateway and OpenAI-compatible chat subset.
- Added strict unknown-price rejection, usage/cost provenance, provider scopes, explicit selection,
  endpoint/secret controls, and no automatic paid retries.
- Used only deterministic mock responses. Real API spend, external inference, dataset acquisition,
  model downloads, trained routing, and claims about quality or savings: none.
- Prepared research-data permission drafts but did not send them.

# 2026-11-19 — Phase 7 Developer Alpha

- Preserved Phase 6G as local commit `40af4a1`; created `codex/phase7`.
- Added deterministic Auto V0 and a real two-server localhost test path.
- Synthetic task/evidence fixtures test correctness only; no empirical gain is reported.
- Added budget reservation/release and strict-SSRF fail-closed configuration.
- External inference, spending, downloads, training and restricted data use: none.

# 2026-11-19 — Phase 7.1 external-provider readiness

- Preserved Phase 7 in local commit `a13e808` and created `codex/phase7-1`.
- Audited current official OpenRouter catalog, model page, routing, rate-limit and pricing material.
- Selected exact `inclusionai/ling-3.2-flash:free`; excluded dynamic router IDs.
- Added a dry-run smoke plan requiring one upstream, disabled fallback and a zero-USD dated price.
- External inference authorization remained `NOT_AUTHORIZED`; requests and spend were zero.
- Proposed v0.2.0a1 only; no version change, push, tag, release, PyPI upload or Phase 8 work.

# 2026-11-19 — Phase 7.1 authorized live-smoke preflight

- Received authorization for exactly one non-streaming OpenRouter request to the pinned free model
  and Ant Digital upstream with an eight-token cap and USD 0 budget.
- Refreshed public availability, pricing, upstream and routing/privacy constraint evidence.
- The process environment did not contain `OPENROUTER_API_KEY`; mandatory authenticated account,
  quota and privacy checks could not run.
- Failed closed before inference: authenticated requests 0, inference requests 0, prompt transfers
  0, retries 0 and spend USD 0.00.

# 2026-11-19 — Phase 7.1 GroqCloud preparation

- Preserved the OpenRouter historical live-smoke report unchanged and added a separate Groq profile.
- Recorded Groq's published standard price instead of treating Free-tier eligibility as zero price.
- Added support and a regression test for official provider base URLs already ending in `/v1`.
- Public-DNS/HTTPS/allowlist endpoint preflight passed without an HTTP request; `GROQ_API_KEY` was
  absent, so account/model/privacy checks could not run.
- Strict zero-budget authorization cannot represent the unverified Free entitlement without
  falsifying pricing; inference, retries, prompt transfers and spend remained zero.
