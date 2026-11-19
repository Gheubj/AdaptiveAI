# Phase 7.1 ProxyAPI Smoke Report

Date: 2026-11-19

Status: **BLOCKED_BY_MISSING_CREDENTIALS**

External inference validation: **not performed**.

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
| Inference authorization | **NOT_AUTHORIZED** |

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

The environment check returned `PROXYAPI_API_KEY_PRESENT=False`. The value was not read, printed,
logged or written. Therefore these mandatory account facts remain unknown:

- whether the key is valid and restricted to `openai/gpt-4.1-mini`;
- whether its one-time provider-side budget is exactly 5 RUB;
- whether balance-read permission is enabled;
- remaining key budget or account balance;
- authenticated `GET /v1/models` availability for this key;
- account-level request logging and retention configuration;
- IP allowlist compatibility with this execution host.

ProxyAPI documents `GET /proxyapi/balance` as permission-gated and states that a budgeted key returns
its remaining key budget instead of the full account balance. No permission was changed and no
authenticated request was attempted. The owner must confirm the model allowlist and one-time 5 RUB
budget in Console if the key lacks balance permission.

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

The current endpoint preflight accepted HTTPS, matched the exact hostname allowlist, resolved only
public addresses, and constructed the correct versioned path. It performed no HTTP request or TLS
handshake and is not evidence of live provider compatibility.

## Request and spend record

- Public documentation/catalog reads: performed without owner content or credentials.
- Authenticated metadata requests: 0.
- Inference requests: 0.
- Prompt transmissions: 0.
- Retries / fallbacks: 0 / 0.
- Provider spend: 0 RUB.
- HTTP status, actual model, response, token usage and latency: not applicable.

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

Expose the dedicated key as `PROXYAPI_API_KEY` in the environment inherited by the task; do not
paste it into chat or a command argument. Then explicitly request read-only preflight. If API access
cannot prove the one-time 5 RUB budget/model restriction, provide confirmation from ProxyAPI Console
without disclosing the key or full balance. Only after every preflight item passes can the status
become `READY_FOR_OWNER_AUTHORIZATION`; paid inference requires a separate exact authorization.

No benchmark, new research phase, package-version change, billing modification, push, tag, release
or publication occurred. Earlier OpenRouter and Groq reports remain unchanged.
