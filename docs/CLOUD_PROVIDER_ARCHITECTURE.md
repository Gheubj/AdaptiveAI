# Cloud Provider Architecture

Phase 6G adds an optional cloud path without coupling it to llama.cpp:

`Client → ProductService → scope guard → CloudGateway → provider adapter → response`

`CloudProvider` exposes configured/discovered models, availability, non-streaming completion, and
streaming. The concrete `OpenAICompatibleProvider` supports `/v1/models` and the documented
chat-completions subset. Identity is `(provider_id, deployment/base_url, model)`, not model name
alone. Configuration distinguishes configured models; discovery intersects advertised models with
the allowlist. “Configured”, “advertised”, and “tested” are not quality evidence. Quality remains
unknown unless an independent evidence record exists.

Selection is deliberately deterministic. Cloud calls require exactly one eligible provider and an
explicit model. Fastest is not inferred without measurements, and Quality never invents ranking.
The `CloudGateway` is the future integration point for Prompt-Aware Router V2, but Phase 6G does not
train or evaluate such a router.

Local requests continue through the unchanged `ModelManager`. `local_only` and local scope take
precedence. Hybrid means cloud is permitted, not silently preferred. No local-to-cloud transition
is automatic.
