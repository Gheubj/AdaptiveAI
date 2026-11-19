# Cloud Gateway Local E2E Validation

Phase 7 starts a real loopback provider and a separate AdaptiveAI HTTP server:

`AdaptiveAIClient → AdaptiveAI socket → ProductService → CloudGateway → httpx socket → test provider`

Verified: discovery, ordinary completion, SSE, usage/missing usage, auth, 400/404/429/503, read
timeout, malformed JSON, interrupted SSE, cancellation, response limit, budget, local-only,
provider allowlist and fallback. Connection refusal maps to unavailable; synthetic transport tests
cover ConnectTimeout. No external host was contacted.

| Feature | Status | Evidence |
|---|---|---|
| Models, JSON chat, SSE | VERIFIED_LOCAL_E2E | Real two-server socket path |
| Usage and common HTTP errors | VERIFIED_LOCAL_E2E | Local deterministic provider |
| Timeout, interruption, cancellation, size | VERIFIED_LOCAL_E2E | Local behavior |
| Connect timeout and redirect policy | MOCK_ONLY | Deterministic unit transport/config |
| Commercial provider | UNKNOWN | No authorized live test |
| Tools/Responses/multimodal | UNSUPPORTED | Outside subset |

Status: `EXTERNAL_PROVIDER_NOT_VALIDATED`.
