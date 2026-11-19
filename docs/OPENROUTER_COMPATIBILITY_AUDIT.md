# OpenRouter Compatibility Audit

Audit date: 2026-11-19. Live inference: **not performed**.

## Official evidence snapshot

- API catalog: `https://openrouter.ai/api/v1/models`
- Exact model page: `https://openrouter.ai/inclusionai/ling-3.2-flash:free`
- Provider routing: `https://openrouter.ai/docs/features/provider-routing`
- Free-model limits: `https://openrouter.ai/docs/api-reference/limits`
- Pricing/account controls: `https://openrouter.ai/pricing`

The catalog exposed exact ID `inclusionai/ling-3.2-flash:free` with prompt and completion prices
`0`; its page identified one serving provider, Ant Digital. Generic `openrouter/free` and
`openrouter/auto` are excluded because they dynamically select models. OpenRouter may otherwise
route among endpoints, so the example sends `provider.only = ["Ant Digital"]` and
`provider.allow_fallbacks = false`.

`provider.data_collection = "deny"` requests endpoints that do not collect data. It is a request
constraint, not proof of account-level Zero Data Retention or contractual privacy. The owner must
verify the dashboard/account policy before execution. A free listing is also not a billing
guarantee; failed attempts may count against rate limits and account limits can vary.

## AdaptiveAI surface

The existing OpenAI-compatible adapter targets `/v1/chat/completions`, supports non-streaming and
SSE streaming, maps typed errors, bounds response size, avoids automatic retries, records reported
usage, and estimates configured cost. `smoke-plan` never instantiates a provider, reads a key, or
opens a network connection.

## Remaining live checks

After separate authorization only: authentication, exact endpoint acceptance, returned model ID,
content shape, usage fields, latency, provider attribution, and actual account charge. Streaming is
a different request and requires separate authorization.

## Compatibility matrix

| Surface | Environment/model | Date | Status |
|---|---|---|---|
| AdaptiveAI OpenAI-shaped HTTP API | local fixture, Python 3.12 | 2026-11-19 | VERIFIED_LOCAL_E2E |
| Official OpenAI Python client | 3.55.1 against installed wheel/local fixture | 2026-11-19 | VERIFIED_LOCAL_E2E |
| OpenRouter ordinary completion | `inclusionai/ling-3.2-flash:free` | 2026-11-19 | UNKNOWN |
| OpenRouter streaming | same | 2026-11-19 | UNKNOWN |
| Other OpenAI-compatible providers | none | — | UNKNOWN |
| Tools, multimodal, Responses API | none | — | UNSUPPORTED |

Mock tests are not external verification. The matrix does not generalize one compatibility result
to other providers, models, revisions or endpoints.
