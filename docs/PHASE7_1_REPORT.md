# Phase 7.1 Report — External Provider Validation & Developer Preview

Date: 2026-11-19. Status: **READY_FOR_OWNER_AUTHORIZATION**.

## Outcome

AdaptiveAI now has a non-network `providers smoke-plan` preflight, a pinned OpenRouter example,
fail-closed checks for an exact model, one upstream, disabled provider fallback, and a dated zero-USD
pricing snapshot. No external inference was executed, no prompt was disclosed, and spend is USD 0.

The proposed single request is deliberately outside this phase's automatic authority. The owner must
separately authorize provider, exact model, request count, streaming choice, maximum cost, prompt
category, and permission to transmit that content. A key being present is not authorization.

## Candidate frozen for authorization

| Field | Frozen value |
|---|---|
| Gateway | OpenRouter |
| Exact model | `inclusionai/ling-3.2-flash:free` |
| Upstream | `Ant Digital` only |
| Provider fallback | disabled |
| Requests | 1 |
| Streaming | no |
| Prompt category | synthetic compatibility phrase; no private/research data |
| Max output | 8 tokens |
| Maximum authorized cost | USD 0.00 |
| Current authorization | `NOT_AUTHORIZED` |

The OpenRouter catalog and model page showed zero prompt/completion price on 2026-11-19. This is a
snapshot, not a billing guarantee; model availability, account eligibility, data policy and price
must be checked immediately before any authorized execution.

## Validation completed without external inference

- 128 tests collected: 125 passed and 3 optional tests skipped on Python 3.12; whole-package
  statement coverage was 71% (Auto V0 95%, cloud adapter 93%, gateway 85%).
- Ruff format/lint and `git diff --check` passed.
- Dry-run configuration/preflight with exact model and upstream pinning.
- The built wheel installed with dependencies into a new `/tmp` venv; `pip check`, CLI help and an
  official OpenAI Python client 3.55.1 local chat-completions request passed.
- Wheel and sdist were built; forbidden planning, raw/processed/model/cache/evidence/vendor/report
  trees were absent. Final artifact sizes and hashes are recorded with the build handoff because
  embedding an archive's own final hash inside that archive is not reproducible.
- Python 3.12 was locally verified; Python 3.11 remains CI-covered but was unavailable locally.

Phase 7's unchanged measurements remain the relevant product baseline: 29.7 microseconds mean router-only overhead over
10,000 synthetic Auto decisions, 1.56 ms mean direct localhost fixture latency over 20 requests,
and 576,356 KiB peak RSS for its coverage run. These are local engineering measurements, not real
LLM latency or minimum memory requirements. Phase 7.1 external latency is unavailable because
external requests were zero.

External model response correctness, live usage accounting, live latency, and live streaming remain
unvalidated until separately authorized. No quality, reliability, savings, or routing-superiority
claim follows from readiness.

## Developer preview recommendation

Proposed future prerelease: `v0.2.0a1`. Do not change the current `0.1.0` package version or publish
until the release checklist is approved. Phase 8 was not started.

## Preview feature and migration summary

| Feature | Preview status |
|---|---|
| Local llama.cpp execution | experimental, optional |
| Cloud-only startup | locally verified |
| Manual / Economy / Auto V0 | locally verified |
| Route explanations | CLI, HTTP and Python client verified locally |
| OpenRouter exact-model config | prepared, external behavior unknown |
| Learned prompt-aware routing | not included |

Migration from public v0.1.0 requires installing a future owner-approved preview artifact; the
public tag must remain immutable. Existing explicit/local modes remain. Auto V0, Economy, Manual,
provider scopes and route explanations are additive preview surfaces. Configuration must keep
credentials in environment variables and must not assume a v0.1.0 wheel contains Phase 7 code.

The runtime dependency audit covers three direct dependencies (`httpx`, `pydantic`, `psutil`), all
resolved from public package indexes in the clean install; `pip check` found no conflicts. The
optional OpenAI client was used only for compatibility testing and is not a runtime dependency.
License inventory remains in `THIRD_PARTY_NOTICES.md`; no dependency or license metadata changed.
