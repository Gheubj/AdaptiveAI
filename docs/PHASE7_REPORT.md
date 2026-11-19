# Phase 7 Engineering Report

## A. Engineering summary

Phase 7 adds replaceable explainable Auto V0, offline task understanding, eligibility-first
selection, strict evidence compatibility, Economy/Manual modes, dry-run CLI/API/SDK, a standalone
localhost provider, real two-server E2E tests, atomic budget reservation and cloud-only startup.

## B. End-to-end gateway

The actual path `AdaptiveAIClient → AdaptiveAI HTTP → CloudGateway → httpx HTTP → local provider`
passed ordinary, SSE, discovery, usage, error, timeout, cancellation, budget and privacy scenarios.
See `CLOUD_GATEWAY_E2E_VALIDATION.md`. This is local protocol validation, not external validation.

## C. Auto Routing V0

Auto V0 can compare candidates only inside one declared compatible evidence group or apply explicit
cost/default policies. Hard constraints run first. The local classifier abstains on ambiguous or
unmatched prompts. Dry-run uses `/v1/route/explain`, the SDK, or `route explain`; it performs no
inference. Explanations report evidence and exclusions without prompt text or credentials.

## D. Synthetic demonstration

With `examples/phase7_alpha.toml`: coding selects `local-e2e-primary` from two comparable synthetic
rows; mathematics and writing return `INSUFFICIENT_EVIDENCE`; an unknown/general prompt also
abstains; local-only returns `NO_ELIGIBLE_CANDIDATE` because this fixture contains only cloud-scope
localhost deployments. These are policy examples, not quality findings.

## E. Security and budgets

Hosted URLs require HTTPS, host allowlists and public preflight DNS; redirects are off; secrets and
prompt content are absent from explanations. The standard transport cannot pin the preflight DNS
address through connection establishment. Strict-SSRF claims therefore fail closed; production
remote use still needs an egress firewall. Explicit localhost development remains valid.

Budget reservations prevent obvious in-process concurrent oversubscription. Estimates are not
billing guarantees; failed/interrupted requests may still be billed. Confirmed billed cost remains
unknown without invoice reconciliation. No potentially chargeable operation is silently retried.

## F. Tests

127 collected: 124 passed, 3 expected skips, 0 failed. Coverage is 71% overall and 95% for Auto V0.
Ruff passed. Wheel/sdist builds and fresh-venv wheel import passed; dependency downloads were
intentionally disabled. Exact hashes are in `PHASE7_TEST_RESULTS.md`.

## G. Performance

10,000 synthetic selections averaged 29.7 microseconds router-only. Twenty direct localhost
provider calls averaged 1.56 ms. Coverage peak RSS was 576,356 KiB. Local synthetic latency cannot
be generalized to real providers or full model inference.

## H. Scientific integrity

Auto V0 cannot infer universal quality, transfer evidence across revisions, claim calibrated
confidence, or establish superiority. Synthetic fixtures validate correctness only. Empirical
comparison of Manual, Cheapest, Strongest, Fastest, task rules and category evidence is
`EMPIRICAL_VALIDATION_NOT_AVAILABLE` without compatible held-out outcomes.

## I. Developer experience

`DEVELOPER_ALPHA_QUICKSTART.md` provides a zero-cost install, provider, gateway, manual/Auto,
explanation, streaming, local-only and pricing-uncertainty path. Python 3.12 was tested; Python 3.11
was unavailable locally.

## J. External provider readiness

`READY_FOR_OPT_IN_LIVE_SMOKE`, with `EXTERNAL_PROVIDER_NOT_VALIDATED`. No live or paid request was
made. The opt-in procedure requires separate owner authorization.

## K. Next milestone

Run one explicitly authorized minimal real-provider compatibility smoke and capture protocol/usage
facts. Do not start Prompt-Aware Router V2 until licensed matched outcomes and complementarity exist.

## L. Git status

Phase 6G is local commit `40af4a1`; Phase 7 is on `codex/phase7` and remains uncommitted pending the
final audit. `planning/`, data, weights, caches and credentials are excluded. Nothing was pushed,
tagged, released or published.
