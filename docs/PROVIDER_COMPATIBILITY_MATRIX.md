# Provider Compatibility Matrix

| Provider/path | Configuration | Discovery | Basic completion | Streaming | Tools | Status |
|---|---:|---:|---:|---:|---:|---|
| Included localhost fixture | Yes | Yes | Yes | Yes | No | `VERIFIED_OFFLINE_FIXTURE` |
| ProxyAPI `openai/gpt-4.1-mini` | Yes | Yes | One live request | Not tested live | Not tested | `VERIFIED_EXTERNAL_BASIC_COMPLETION` |
| OpenRouter prepared config | Yes | Preflight only | Not executed | Not executed | Not tested | `CONFIGURATION_AUDITED` |
| Groq prepared config | Yes | Preflight only | Not executed | Not executed | Not tested | `CONFIGURATION_AUDITED` |
| Other OpenAI-compatible services | Generic interface | Provider-dependent | Unverified | Fixture-tested only | Not supported | `UNVERIFIED` |

The ProxyAPI request returned `ok` in 0.7832 seconds, with 0.001661 RUB confirmed against the
provider-key budget. Raw upstream status/model and numeric token counts were not independently
recorded. Compatibility never implies quality, reliability, savings or production readiness.
