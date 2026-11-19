# Developer Alpha Quick Start

This zero-cost path uses synthetic evidence and two localhost processes.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[test]'
export ADAPTIVEAI_E2E_KEY=local-test-key
.venv/bin/python -m adaptiveai.test_provider --port 8099
```

Second terminal:

```bash
export ADAPTIVEAI_E2E_KEY=local-test-key
.venv/bin/adaptiveai --config examples/phase7_alpha.toml serve
.venv/bin/adaptiveai --config examples/phase7_alpha.toml route explain \
  'Debug this Python function' --mode auto --scope hybrid --max-estimated-cost 0.01
```

Manual request:

```bash
curl http://127.0.0.1:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"local-e2e","provider":"local-e2e","provider_scope":"cloud","local_only":false,"max_estimated_cost":0.01,"messages":[{"role":"user","content":"hello"}]}'
```

For Auto use `model=auto`, `routing_mode=auto`, `provider_scope=hybrid`, `local_only=false` and a
budget. Add `stream=true` for SSE. Omit `local_only=false` to verify rejection. General prompts
return `INSUFFICIENT_EVIDENCE` because the fixture has synthetic coding evidence only.

An OpenAI Python client may use `base_url="http://127.0.0.1:8088/v1"` and pass AdaptiveAI controls
through `extra_body`. Verified subset: models, chat completions and streaming. Tools, multimodal and
Responses API are unsupported. Diagnostics are an AdaptiveAI extension. No IDE integration was
validated; tools supporting custom base URL and extra fields are candidates for later testing.
