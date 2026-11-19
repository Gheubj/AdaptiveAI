# Developer Preview Quick Start

AdaptiveAI is experimental and local-first. Python 3.11 or 3.12 is supported.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
adaptiveai doctor
pytest -q
```

After an owner-approved preview is public, a source install may use the exact preview tag rather
than the old public v0.1.0 tag. Until then, use the local checkout or locally built wheel; v0.1.0
does not contain Auto V0.

## A — Offline demonstration

Run the deterministic localhost provider example from
`examples/phase7_alpha.toml` for an end-to-end path that cannot incur cloud cost. See
`docs/DEVELOPER_ALPHA_QUICKSTART.md` for the two local servers and Auto V0 examples.

That walkthrough covers Manual, Auto V0, SSE streaming, route explanations and a local-only cloud
rejection using synthetic fixtures and no API key from an external service.

## B — Real cloud provider (authorization gated)

To inspect the proposed OpenRouter smoke without sending anything:

```bash
adaptiveai --config examples/openrouter_phase7_1.toml providers smoke-plan \
  --provider openrouter --model inclusionai/ling-3.2-flash:free \
  --input-tokens 16 --max-output-tokens 8
```

Expected status is `READY_FOR_OWNER_AUTHORIZATION` and `executes_inference` is `false`. Do not run
`chat --scope cloud` until the exact authorization record is separately approved. Never store API
keys in TOML, shell history, examples, logs, issues, or commits.

After authorization, set `OPENROUTER_API_KEY` in the process environment, rerun list/estimate/plan,
and execute only the approved request count, model, stream setting, prompt category and cost. Read
the returned `routing` diagnostics; never treat the locally estimated cost as the final provider
bill. No such request has yet been authorized or tested.

## C — Optional local models

Local GGUF execution requires a separately built pinned llama.cpp server plus a registry whose paths
and hashes match local model files. Configure `backend_path` and `registry_path`, run
`adaptiveai hardware inspect` and `adaptiveai models list --verify-hashes`, then use `chat` with
`--scope local`. Model weights are not bundled or downloaded automatically. Cloud-only users do not
need llama.cpp, GGUF files or research dependencies.

## OpenAI-compatible Python client

OpenAI-compatible clients use `http://127.0.0.1:8088/v1` as `base_url`; the API key value is ignored
by the local server but client libraries may require a non-empty placeholder. AdaptiveAI extensions
such as routing diagnostics are present in the raw response and may not be surfaced by every SDK.
Use `chat.completions.create`; pass `routing_mode`, `provider_scope`, budgets and routing controls
through `extra_body`. Streaming chat completions are supported; tools, multimodal input, embeddings,
Assistants and Responses API are not. `/v1/route/explain` is an AdaptiveAI endpoint, not a standard
OpenAI SDK resource. Errors use an OpenAI-shaped JSON body, but compatibility with every SDK error
subclass is not claimed.
