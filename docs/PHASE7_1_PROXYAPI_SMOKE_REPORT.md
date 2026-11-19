# Phase 7.1 ProxyAPI Smoke Report

Date: 2026-11-19

Status: **EXTERNAL_PROVIDER_VALIDATED**

External inference validation: **performed exactly once**.

## Prepared operation

| Field | Prepared value |
|---|---|
| Provider | ProxyAPI |
| Base URL | `https://api.proxyapi.ru/v1` |
| Chat endpoint | `https://api.proxyapi.ru/v1/chat/completions` |
| Exact model | `openai/gpt-4.1-mini` |
| Credential environment | `PROXYAPI_API_KEY` |
| Request | one non-streaming Chat Completion |
| Prompt | `Reply with exactly: ok` |
| Maximum output | 16 tokens |
| Tools / fallback / retries | none / none / none |
| Proposed request ceiling | 5 RUB |
| Inference authorization | explicitly authorized and consumed for exactly one request |

The example is `examples/proxyapi_phase7_1.toml`. No credential or private account metadata is
stored in it. The existing provider-independent OpenAI-compatible adapter is reused; no ProxyAPI SDK
or parallel provider framework was added.

## Official catalog and API evidence

The current official ProxyAPI catalog lists exact model `openai/gpt-4.1-mini`, context 1.05M,
input 104 RUB per million tokens and output 413 RUB per million tokens. The catalog states that
prices include 5% VAT. ProxyAPI's current documentation identifies `https://api.proxyapi.ru/v1` as
the unified OpenAI-compatible base URL, Bearer authorization, `GET /v1/models`, and proportional
RUB billing from actual usage.

Pricing is stored as exact decimal RUB values with source and retrieval date. It is never interpreted
as USD, converted, or treated as free. A conservative 16-input/16-output estimate is exactly
0.008272 RUB. The real input estimate for the proposed prompt is calculated by AdaptiveAI's
documented conservative character heuristic; provider tokenization and the provider's final charge
may differ.

## Currency-aware budget change

The existing budget implementation previously rejected all non-USD prices. It now:

- uses `Decimal` for configured prices, estimates, reservations and committed usage;
- carries an explicit three-letter pricing currency;
- requires the request's `cost_currency` to match provider pricing;
- binds each ledger to one currency and rejects mixed-currency reservations;
- performs no implicit FX conversion;
- emits currency alongside routing cost diagnostics;
- preserves the existing strict unknown-price rejection and atomic reservation lock.

The proposed command will require both `--max-estimated-cost 5` and `--cost-currency RUB`. This is
client-side protection only. It does not prove or replace the requested one-time 5 RUB provider-key
budget.

## Deterministic offline validation

The local MockTransport contract covers the exact `/v1` URL, model ID, Bearer header, ordinary
response, usage and missing usage, RUB estimates, reservation/release, zero-budget and currency
rejection, 401, 402, 403, 429, 502, 504, disabled retry, empty fallback list, local-only rejection,
and secret-free errors. It sends no internet request.

The compatibility adapter supports provider roots that already end in `/v1`, so it produces
`/v1/chat/completions`, never `/v1/v1/chat/completions`. Redirect following remains disabled.

Final offline verification on Python 3.12.3 collected 130 tests: 127 passed and 3 expected opt-in
tests skipped. Whole-package statement coverage was 71%; cloud adapter coverage was 94% and gateway
coverage 90%. Ruff formatting/lint, `git diff --check`, package build, clean wheel installation,
`pip check`, CLI estimate, SDK and local HTTP E2E tests passed. Python 3.11 was not installed locally
and is not claimed as executed here.

## Read-only preflight

The owner supplied a newly entered credential through a hidden interactive terminal prompt. The
environment check returned `PROXYAPI_API_KEY_PRESENT=true`; the value was not printed, logged,
written to disk or included in a command argument.

After an initial rejected credential was replaced and its balance permission enabled, authenticated,
read-only metadata preflight was repeated with redirects disabled, a 15-second timeout and a
one-megabyte response bound. The final results were:

- `GET https://api.proxyapi.ru/v1/models` returned HTTP 200 and included exact model
  `openai/gpt-4.1-mini`;
- `GET https://api.proxyapi.ru/proxyapi/balance` returned HTTP 200 and reported a 5.0 RUB key budget
  with 0.0 RUB used.

No response body was logged. The successful model listing validates the credential and exact-model
access. The balance endpoint independently validates the provider-side spending ceiling and unused
starting state. The owner stated that all requested key restrictions were configured, including the
exact-model restriction. Account-level request logging and retention are not exposed by these API
responses and remain owner-controlled Console settings.

The successful authenticated model request confirms that the current execution host is compatible
with the configured IP restriction, if one is enabled.

ProxyAPI documents `GET /proxyapi/balance` as permission-gated and states that a budgeted key returns
its remaining key budget instead of the full account balance. The final response confirmed the
dedicated 5 RUB key budget without requiring disclosure of the full account balance.

ProxyAPI also documents optional account-wide full request/response logging, including prompts and
outputs, with configurable retention and possible logging charges. Its state cannot be inferred
without account access. The proposed prompt is synthetic, but the owner should confirm the desired
logging setting before authorizing inference.

## Security review

Preserved controls: HTTPS-only hosted endpoint, exact `api.proxyapi.ru` hostname allowlist, exact
model/provider selection, environment-only credential, redirect rejection, bounded timeouts and
response size, local-only enforcement, no automatic retry, and no implicit fallback. Errors never
include response bodies or credentials.

The standard hosted policy performs DNS preflight but does not pin the resolved address at connect
time; it is not network-layer SSRF protection. Setting `strict_ssrf_protection=true` continues to
fail closed because the current transport lacks connection pinning or an egress firewall. This
limitation was not weakened or described as production-hardened security.

The initial offline endpoint preflight accepted HTTPS, matched the exact hostname allowlist,
resolved only public addresses, and constructed the correct versioned path. That check itself
performed no HTTP request or TLS handshake; the later authenticated metadata and single inference
request provide the live compatibility evidence documented below.

## Live validation result

After successful preflight, the owner explicitly authorized exactly one non-streaming inference
request with the prepared prompt, exact model, 16-token maximum, no retry or fallback and a 5 RUB
ceiling. The command used the real AdaptiveAI Gateway CLI and the checked-in ProxyAPI configuration;
it did not call a provider SDK directly.

| Field | Observed result |
|---|---|
| Gateway/provider | AdaptiveAI Gateway → ProxyAPI |
| Requested model | `openai/gpt-4.1-mini` |
| Selected model | `openai/gpt-4.1-mini` |
| Provider | `proxyapi` |
| Prompt | `Reply with exactly: ok` |
| Returned text | `ok` |
| Completion success / HTTP interpretation | successful completion; HTTP success implied, raw status not surfaced by CLI |
| Maximum output tokens | 16 |
| Token counts | not surfaced by the current CLI output |
| Measured latency | 0.7832133880001493 seconds |
| Pre-request estimate | 0.007648 RUB |
| Provider-usage actual cost | 0.001661 RUB |
| Post-request key-budget usage | 0.001661 RUB of 5.0 RUB |
| Usage source | `provider` |
| Fallback | none (`fallback_reason: null`) |
| Retry | none |

The post-request read-only balance check independently matched AdaptiveAI's reported actual cost:
the provider-key budget changed from 0.0 RUB used to 0.001661 RUB used. The CLI reports the exact
requested/selected model but does not expose the raw provider response's `model` field, so raw
response-model identity is not independently claimed. No credential appeared in terminal output or
the report.

## Request and spend record

- Public documentation/catalog reads: performed without owner content or credentials.
- Final authenticated metadata preflight: 2 read-only GET requests; both returned HTTP 200. An
  earlier attempt returned models HTTP 200 and balance HTTP 403 before balance permission was enabled.
- Inference requests: exactly 1.
- Prompt transmissions: exactly 1 synthetic prompt.
- Retries / fallbacks: 0 / 0.
- Provider spend: 0.001661 RUB, confirmed by both provider-derived gateway accounting and the
  post-request key-budget delta.
- Returned text: `ok`.
- Measured latency: 0.7832133880001493 seconds.
- Raw HTTP status, raw response model and numeric token counts were not surfaced by the CLI.

## Next gate

Install the future preview from its owner-approved artifact; until publication, use the local wheel
or checkout. The old public v0.1.0 does not contain this Phase 7.1 work. Safe local inspection:

```bash
# PROXYAPI_API_KEY must already be present in the inherited process environment.
adaptiveai --config examples/proxyapi_phase7_1.toml providers list
adaptiveai --config examples/proxyapi_phase7_1.toml providers estimate \
  --provider proxyapi --model openai/gpt-4.1-mini \
  --input-tokens 16 --max-output-tokens 16
```

After successful read-only preflight and separate paid-request authorization, the single prepared
command is:

```bash
adaptiveai --config examples/proxyapi_phase7_1.toml chat 'Reply with exactly: ok' \
  --scope cloud --provider proxyapi --model openai/gpt-4.1-mini \
  --max-tokens 16 --max-estimated-cost 5 --cost-currency RUB --allow-paid-cloud
```

This command is documentation only and was not executed.

The authorized request has been consumed and must not be repeated under the same authorization.
ProxyAPI compatibility is externally validated for this narrow path. Account logging/retention
remains an owner-controlled Console setting and should stay at the owner-approved value. Broader
provider reliability, streaming, tool calls, concurrency, failure handling and benchmark quality
remain unvalidated.

No benchmark, new research phase, package-version change, billing modification, push, tag, release
or publication occurred. Earlier OpenRouter and Groq reports remain unchanged.
