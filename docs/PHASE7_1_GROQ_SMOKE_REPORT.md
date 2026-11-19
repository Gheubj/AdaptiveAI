# Phase 7.1 GroqCloud Smoke Report

Date: 2026-11-19

Final status: **BLOCKED_BY_BUDGET**

External inference validation: **not performed**.

## Prepared operation

| Field | Value |
|---|---|
| Provider | GroqCloud |
| API root | `https://api.groq.com/openai/v1` |
| Exact model | `openai/gpt-oss-20b` |
| Credential reference | `GROQ_API_KEY` |
| Account claim | owner states Groq Free tier; API verification unavailable |
| Proposed inference | one non-streaming Chat Completion |
| Prompt | `Reply with exactly: ok` |
| Maximum output | 16 tokens |
| Retries / fallback | none / none |
| Authorized spend | USD 0.00 |
| Inference authorization | **NOT_AUTHORIZED** (preflight only) |

The separate configuration is `examples/groq_phase7_1.toml`. It has no OpenRouter routing fields,
contains one allowlisted model, uses HTTPS and an exact hostname allowlist, limits the client to one
request per minute, and retains existing timeout, response-size, local-only, redaction and budget
controls. The adapter now accepts providers whose documented base URL already ends in `/v1` without
constructing a duplicate `/v1/v1` path. No gateway redesign or Groq SDK was introduced.

## Public evidence preflight

Groq's official model documentation currently lists `openai/gpt-oss-20b` as supported for Chat
Completions, with a 131,072-token context and 65,536 maximum output tokens. The published standard
price is USD 0.075 per million input tokens and USD 0.30 per million output tokens. The price was
preserved exactly in configuration; it was not changed to zero.

Groq's public Free-plan rate-limit table lists 30 RPM, 1,000 RPD, 8,000 TPM and 200,000 TPD for this
model, while explicitly warning that exact organization limits must be checked on the account's
Limits page. The proposed 16-token output cap fits the public numerical limits but does not prove
the owner's current remaining quota or entitlement.

Groq documents HTTPS Chat Completions and authenticated `GET /models`. It states that inference
inputs/outputs are not retained by default except temporary reliability/abuse logging for up to 30
days, and that organization admins may enable Zero Data Retention in Console Data Controls. There
is no OpenRouter-style per-request `data_collection` field, so none is sent. Account-level ZDR and
Data Controls could not be inspected.

The local endpoint-security preflight accepted only HTTPS, matched the explicit `api.groq.com`
allowlist, resolved the hostname to public addresses, rejected redirects by client policy, and
constructed `/openai/v1/models` without duplicating the version segment. This does not claim
connection pinning or network-layer SSRF protection, and no HTTP request or TLS handshake was made.

## Account preflight

The process environment check returned `GROQ_API_KEY_PRESENT=False`; the value was never read or
printed. Consequently no authenticated model-list request was made and these mandatory facts remain
unknown:

- actual account tier and whether a payment method/paid Developer plan is active;
- exact organization rate limits and remaining quota;
- whether `openai/gpt-oss-20b` is available to this organization/region;
- account Data Controls and ZDR state;
- billing status and independently verifiable Free-tier eligibility.

## Strict zero-budget incompatibility

AdaptiveAI's strict budget authorizes from model price and conservative input/output token bounds.
With the truthful published prices, the proposed request has a positive worst-case estimate. A
`max_estimated_cost = 0` request is therefore rejected before inference. The current schema has no
independently verified Free-tier entitlement object and cannot prove that a normally priced model
will be free for this account/request.

Setting both prices to zero would falsify provider metadata. Disabling strict budget or raising the
budget would violate the owner's USD 0 authorization. Groq spending limits cannot solve this: Groq
documents them as a paid-plan-only feature, whereas the requested account condition is Free tier.
No bypass or billing change was attempted.

Illustrative conservative estimate for 16 estimated input tokens and 16 maximum output tokens:
USD 0.000006. The actual prompt tokenization is provider-dependent, so this estimate is not a bill.

## Requests, cost and validation status

- Public documentation lookups: performed without credentials or prompt content.
- Authenticated metadata requests: 0.
- Inference requests: 0.
- Retries/fallbacks: 0/0.
- Prompt transmissions: 0.
- Spend: USD 0.00.
- HTTP status, actual response model, text, usage and latency: not applicable.
- Confirmed: configuration validation, exact endpoint construction, allowlists, local budget
  rejection behavior and public-DNS endpoint preflight.
- Unconfirmed: Groq account eligibility, live API compatibility, model availability, privacy state,
  response parsing, usage accounting and billing outcome.

## Required resolution

First, expose `GROQ_API_KEY` only through the inherited process environment so authenticated
read-only account/model checks can run. Separately, the owner must choose a budget policy that does
not falsify price metadata. Under the current USD 0 authorization and strict price-based gateway,
the request cannot advance to `READY_FOR_OWNER_AUTHORIZATION` even if the Free account is later
confirmed.

No benchmark, new development phase, package-version change, push, tag, release, PyPI publication,
credit purchase or billing-setting change was performed. The historical OpenRouter live-smoke
report was not modified.
