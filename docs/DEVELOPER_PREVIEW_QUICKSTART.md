# Developer Preview Quick Start — 0.2.0a1

AdaptiveAI is experimental. Python 3.11 or 3.12 is required. No API key, model weight, research
archive or llama.cpp installation is needed for the offline demo.

## Install the published preview

Install directly from the immutable public tag:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install "git+https://github.com/Gheubj/AdaptiveAI.git@v0.2.0a1"
adaptiveai --version
```

Or download `adaptiveai-0.2.0a1-py3-none-any.whl` from the
[v0.2.0a1 release](https://github.com/Gheubj/AdaptiveAI/releases/tag/v0.2.0a1):

```bash
python -m pip install ./adaptiveai-0.2.0a1-py3-none-any.whl
```

Both methods install the Python package. The walkthrough below also needs the public example TOML,
so use a source checkout at the same tag. This does not install research dependencies or weights.

## A — Offline gateway demo

```bash
git clone --branch v0.2.0a1 --depth 1 https://github.com/Gheubj/AdaptiveAI.git
cd AdaptiveAI
export ADAPTIVEAI_E2E_KEY=local-test-key
adaptiveai --config examples/phase7_alpha.toml doctor
```

Start the included deterministic provider in terminal 1:

```bash
export ADAPTIVEAI_E2E_KEY=local-test-key
python -m adaptiveai.test_provider --host 127.0.0.1 --port 8099
```

Start the gateway in terminal 2:

```bash
cd AdaptiveAI
export ADAPTIVEAI_E2E_KEY=local-test-key
adaptiveai --config examples/phase7_alpha.toml serve --host 127.0.0.1 --port 8088
```

From terminal 3, run the complete zero-cost checks in
`docs/DEVELOPER_ALPHA_QUICKSTART.md`. All responses and evidence are synthetic.

The official OpenAI Python SDK example is `examples/openai_sdk_local.py`. Supported compatibility is
limited to chat completions and streaming. Tools, multimodal input, embeddings, Assistants and the
Responses API are not supported.

## B — OpenAI-compatible cloud BYOK

Copy `examples/proxyapi_phase7_1.toml` to a private local file, change provider/model/pricing to
current values from your provider,
keep the endpoint and deployment allowlists narrow, and name an environment variable rather than a
credential value. Never commit keys.

```bash
read -rsp "Provider API key: " MY_PROVIDER_API_KEY && export MY_PROVIDER_API_KEY && echo
adaptiveai --config adaptiveai.toml providers list
adaptiveai --config adaptiveai.toml providers estimate \
  --provider my-provider --model exact-model --input-tokens 32 --max-output-tokens 32
adaptiveai --config adaptiveai.toml route explain 'Summarize this' --mode auto --scope cloud
```

Set `api_key_env = "MY_PROVIDER_API_KEY"` in the private TOML so the configuration and exported
variable match. The placeholder name is not tied to ProxyAPI or another provider.

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

Optional feedback can use `docs/EXTERNAL_TESTER_FEEDBACK.md`. Remove credentials, private prompts,
provider responses and account identifiers before sharing it.
