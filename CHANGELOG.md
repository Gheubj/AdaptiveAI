# Changelog

## 0.2.0a1 — Developer Preview release candidate, not released

- Added provider-independent OpenAI-compatible BYOK gateway, local/cloud/hybrid scopes, explicit
  fallback, usage accounting and currency-aware budget enforcement.
- Added deterministic Auto V0, Economy and Manual routing with dry-run and route explanations.
- Added Model Intelligence identities, capability/evidence/permission infrastructure and external
  benchmark adapters.
- Added routing-supervision and matched-outcome research infrastructure without claiming learned
  routing superiority.
- Verified one real ProxyAPI basic completion; external streaming, tools, concurrency and
  reliability remain unverified.
- Preserved local llama.cpp/GGUF modes and the immutable public v0.1.0 release.

Migration from v0.1.0 is additive but configuration-aware: cloud access is opt-in, credentials stay
in environment variables, paid requests require explicit acknowledgement and currency-matched
budgets, and Auto V0 may abstain with `INSUFFICIENT_EVIDENCE`.

## 0.1.0-rc1 — 2026-11-18

- Added public types, validated configuration, four routing modes, and explicit selection.
- Added lifecycle hysteresis, dynamic ports, bounded concurrency, cleanup, and errors.
- Added doctor/hardware/models/serve/chat CLI, API subset, SSE, client, examples, CI, and packaging.
- Preserved Phase 1–4.5 findings without claiming routing superiority.
