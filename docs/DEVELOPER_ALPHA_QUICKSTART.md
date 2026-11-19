# Developer Alpha Quick Start

This zero-cost path uses synthetic evidence and two localhost processes. Run it from a checkout of
the same version you installed, such as public tag `v0.2.0a1`.

```bash
export ADAPTIVEAI_E2E_KEY=local-test-key
python -m adaptiveai.test_provider --port 8099
```

Second terminal:

```bash
export ADAPTIVEAI_E2E_KEY=local-test-key
adaptiveai --config examples/phase7_alpha.toml serve
```

Manual request:

```bash
curl http://127.0.0.1:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"local-e2e","provider":"local-e2e","provider_scope":"cloud","local_only":false,"max_estimated_cost":0.01,"messages":[{"role":"user","content":"hello"}]}'
```

Auto V0 request:

```bash
curl http://127.0.0.1:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"auto","routing_mode":"auto","provider_scope":"hybrid","local_only":false,"max_estimated_cost":0.01,"messages":[{"role":"user","content":"Debug this Python function"}]}'
```

Inspect the decision without inference:

```bash
adaptiveai --config examples/phase7_alpha.toml route explain \
  'Debug this Python function' --mode auto --scope hybrid --max-estimated-cost 0.01
```

Streaming:

```bash
curl -N http://127.0.0.1:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"local-e2e","provider":"local-e2e","provider_scope":"cloud","local_only":false,"stream":true,"max_estimated_cost":0.01,"messages":[{"role":"user","content":"hello"}]}'
```

Local-only rejection (expected error; no provider call):

```bash
curl http://127.0.0.1:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"local-e2e","provider":"local-e2e","provider_scope":"cloud","local_only":true,"max_estimated_cost":0.01,"messages":[{"role":"user","content":"hello"}]}'
```

General Auto prompts may return `INSUFFICIENT_EVIDENCE` because the fixture has synthetic coding
evidence only. This is expected abstention, not a validated intelligent-router result.

An OpenAI Python client may use `base_url="http://127.0.0.1:8088/v1"` and pass AdaptiveAI controls
through `extra_body`. Verified subset: models, chat completions and streaming. Tools, multimodal and
Responses API are unsupported. Diagnostics are an AdaptiveAI extension. No IDE integration was
validated; tools supporting custom base URL and extra fields are candidates for later testing.
