# API Reference

AdaptiveAI implements a documented OpenAI-compatible subset:

- `GET /health`: service and lifecycle health.
- `GET /v1/models`: configured models and availability.
- `POST /v1/chat/completions`: `messages`, optional explicit `model` (`auto` routes),
  `routing_mode`, `temperature`, `max_tokens`, `stream`, `timeout`, `local_only`, latency, and RAM.

Non-streaming responses contain `choices`, nullable token `usage`, and routing diagnostics.
Streaming uses `text/event-stream`, content chunks, a final diagnostic chunk, and `[DONE]`. Client
disconnect closes the upstream stream and never causes an automatic duplicate retry.

Errors use `{"error":{"type":"...","message":"..."}}`: 400 validation/routing, 413 size, 429
concurrency, 503 backend, or 504 timeout. Unknown fields are rejected. Unsupported: tools,
multimodal input, logprobs, multiple choices, JSON schema mode, embeddings, authentication, and full
OpenAI parity.
