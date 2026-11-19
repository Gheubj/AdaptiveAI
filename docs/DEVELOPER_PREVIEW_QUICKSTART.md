# Developer Preview Quick Start — 0.2.0a1

AdaptiveAI is experimental. Python 3.11 or 3.12 is required. Until publication, install the locally
built wheel; no API key, model weight, research archive or llama.cpp installation is needed for the
offline demo.

## A — Offline gateway demo

```bash
python -m venv .venv && . .venv/bin/activate
python -m pip install dist/adaptiveai-0.2.0a1-py3-none-any.whl
adaptiveai --version
adaptiveai --config examples/phase7_alpha.toml doctor
```

From the source checkout, start the included deterministic provider and gateway in two terminals:

```bash
python -m adaptiveai.test_provider --host 127.0.0.1 --port 18089
adaptiveai --config examples/phase7_alpha.toml serve --host 127.0.0.1 --port 8088
```

Then follow `docs/DEVELOPER_ALPHA_QUICKSTART.md` for Manual, Auto V0, `/v1/route/explain`, SSE
streaming and the expected local-only rejection. All responses are synthetic and cost zero.

The official OpenAI Python SDK example is `examples/openai_sdk_local.py`. Supported compatibility is
limited to chat completions and streaming. Tools, multimodal input, embeddings, Assistants and the
Responses API are not supported.

## B — OpenAI-compatible cloud BYOK

Copy `examples/proxyapi_phase7_1.toml`, change provider/model/pricing to values from your provider,
keep the endpoint and deployment allowlists narrow, and name an environment variable rather than a
credential value. Never commit keys.

```bash
export MY_PROVIDER_API_KEY='set outside shell history where possible'
adaptiveai --config adaptiveai.toml providers list
adaptiveai --config adaptiveai.toml providers estimate \
  --provider my-provider --model exact-model --input-tokens 32 --max-output-tokens 32
adaptiveai --config adaptiveai.toml route explain 'Summarize this' --mode auto --scope cloud
```

Only after reviewing the plan should an owner issue a chat command with an explicit provider,
model, currency-matched ceiling and `--allow-paid-cloud`. Empty fallback lists mean no fallback.
Unknown price fails closed. Local estimates are conservative controls, not billing guarantees.

ProxyAPI has status `VERIFIED_EXTERNAL_BASIC_COMPLETION` for one exact non-streaming request only.
No example or automated test performs paid inference.

## C — Optional local GGUF

Build or provide a compatible `llama-server`, obtain GGUF weights under their own terms, and set
`backend_path` plus `registry_path` in a copied configuration. AdaptiveAI never downloads weights.

```bash
adaptiveai --config adaptiveai.toml hardware inspect
adaptiveai --config adaptiveai.toml models list --verify-hashes
adaptiveai --config adaptiveai.toml chat 'Reply with ready' --scope local --mode fastest
```

Profiles are host/workload specific. The lifecycle manager keeps at most one configured local model
resident and applies stickiness/hysteresis; switching overhead can erase routing gains. Cloud-only
use does not require llama.cpp or the optional `research` dependencies.
