# Phase 7.1 Live Smoke Report

Date: 2026-11-19

Result: **BLOCKED_AT_PREFLIGHT — NO CREDENTIAL IN PROCESS ENVIRONMENT**

## Authorized operation

| Field | Authorized value |
|---|---|
| Gateway | OpenRouter through AdaptiveAI |
| Model | `inclusionai/ling-3.2-flash:free` |
| Upstream | `Ant Digital` only |
| Inference requests | exactly 1 |
| Streaming | disabled |
| Prompt | `Reply with exactly: ok` |
| Maximum output | 8 tokens |
| Maximum cost | USD 0.00 |
| Provider fallback | disabled |
| Data collection | deny |
| Automatic retry | disabled |

## Preflight result

Public OpenRouter metadata was refreshed on 2026-11-19. The exact model remained listed as free
for both input and output and the model page listed Ant Digital as its single serving provider.
Current public availability was shown, and the prepared AdaptiveAI configuration still pins
`provider.only = ["Ant Digital"]`, `allow_fallbacks = false`, `data_collection = "deny"`, one
client-side request per minute, and a zero-USD pricing snapshot.

The process environment check returned `OPENROUTER_API_KEY_PRESENT=False`. The value of the key was
never requested, read, printed, logged, or written. Without a credential in the process environment,
AdaptiveAI cannot perform authenticated read-only account/key checks for account eligibility,
quota, credit/spending limits, or privacy settings. These were mandatory owner conditions, so the
preflight failed closed before provider construction or inference.

## Network and cost accounting

- Public documentation/catalog lookups: performed without owner content and without an API key.
- Authenticated account requests: 0.
- Inference requests: 0.
- Automatic retries: 0.
- Prompt transmissions to OpenRouter or Ant Digital: 0.
- Provider HTTP status: not applicable.
- Input/output tokens: not applicable.
- External latency: not measured.
- Estimated and actual inference cost: USD 0.00.
- Fallback: not attempted.
- Key exposure: none; no key was available to the process.

## Confirmed capabilities

- Non-network AdaptiveAI smoke planning fails closed with exact-model, upstream, privacy, fallback,
  output-token and zero-price constraints.
- Current public metadata identifies the exact free model and Ant Digital upstream.
- The authorization was not interpreted as permission to bypass account preflight.

## Unconfirmed capabilities

- Owner-account eligibility and current quota/limits.
- Whether the owner's key is restricted to zero spend.
- Account-level privacy/ZDR settings.
- Authenticated visibility of the exact model/upstream.
- Real AdaptiveAI-to-OpenRouter request serialization and response parsing.
- HTTP status, returned model ID, upstream attribution, usage, latency and billing outcome.

## Errors and required action

This is an environment/configuration blocker, not an AdaptiveAI inference failure. Export the key as
`OPENROUTER_API_KEY` into the environment inherited by the Codex task and resume this same bounded
authorization. Do not paste the secret into chat, a command argument, a TOML file, shell history, or
the repository. After the key becomes available, repeat the full preflight; do not reuse the public
metadata result as proof of account eligibility.

No code fix, security relaxation, billing change, credit purchase, benchmark, new development phase,
push, tag, release, PyPI publication, or v0.1.0 modification was performed.

Developer Preview conclusion: the offline release candidate remains prepared, but external-provider
validation is incomplete. AdaptiveAI is not yet ready to advance past the Phase 7.1 live-smoke gate.
