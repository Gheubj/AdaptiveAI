# Phase 6G Report

## A. Decision

Phase 6G implements a usable experimental BYOK gateway while retaining local-first behavior. It is
not a production security certification and makes no cloud quality, routing-superiority, or saving
claim.

## B. Architecture and provider support

The provider interface and OpenAI-compatible adapter support allowlisted model configuration,
explicit discovery, availability, ordinary and SSE completion, usage, typed errors, timeouts, and
stream closure. Provider/deployment/model identity is explicit. Configured or advertised models do
not receive invented quality evidence.

## C. Security and privacy

Keys are environment references and are not persisted or logged. Hosted URLs require HTTPS, exact
host allowlists, public DNS results, bounded responses, no redirects, and bounded timeouts. Local
HTTP requires explicit developer mode. Prompts/responses are absent from usage records by default.

## D. Routing behavior

Local-only has precedence. Cloud requires explicit provider and model. Hybrid grants permission but
does not silently choose cloud. Unknown fastest/quality comparisons are rejected rather than
fabricated. Explicit fallback is limited and never retries ambiguous billable failures.

## E. Pricing, usage, and budgets

Input/output rates include currency, source, and retrieval date. Unknown price is not zero. Strict
mode rejects it. Worst-case per-request and cumulative limits run before transmission. Provider
usage can support a post-response calculation, which is not claimed to equal the final invoice.

## F. API, CLI, and SDK

The existing OpenAI-style server accepts scope/provider/budget fields and exposes `/v1/providers`.
The Python client supports the same fields and streaming. CLI offers offline `providers list`; cloud
chat requires `--allow-paid-cloud`. Startup, doctor, install, inspection, and tests do not infer.

## G. Research data access

Unsent xRouteBench and RoutingCompendium permission drafts are in
`RESEARCH_DATA_PERMISSION_REQUESTS.md`. Dataset restrictions from Phase 6B.5 remain unchanged.

## H. Tests

106 passed and 3 expected skips from 109 collected tests. Whole-package coverage is 70%; the two
new cloud modules have approximately 87% combined statement coverage. Ruff formatting/lint passed.
Wheel and sdist builds passed, and the wheel imported from a fresh venv using the existing offline
dependency set. Full details and the dependency-install qualification are in
`PHASE6G_TEST_RESULTS.md`.

## I. Resources

Paid API spend: USD 0. Model downloads: none. External cloud/dataset calls: none. Mock responses are
deterministic and in-process. Coverage-suite peak RSS was 576,996 KiB and elapsed time was 20.49
seconds.

## J. Next research stage

Prompt-Aware Router V2 prerequisites and permission boundaries are documented in
`NEXT_ROUTING_RESEARCH_PLAN.md`. It was not implemented.

## K. Git status

Phase 6B.5 commit: `5d7e650`. Phase 6G branch: `codex/phase6g`. `planning/`, private evidence,
caches, model weights, and datasets remain excluded. Phase 6G is local and uncommitted until final
verification; nothing was pushed, tagged, released, or published.
