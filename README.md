# AdaptiveAI

**AdaptiveAI 0.2.0a1 is an experimental Developer Preview for local and BYOK LLM routing.**

AdaptiveAI is an **experimental, local-first LLM routing framework**. It provides one observable
interface for llama.cpp models and selects eligible models by measured latency, validation-defined
quality, a documented balanced objective, or hardware constraints.

AdaptiveAI is not a proven universal inference optimizer and is not production hardened.

Use it to put local llama.cpp deployments and explicitly configured OpenAI-compatible cloud
providers behind one observable gateway, enforce eligibility and budget constraints, and inspect
why the deterministic Auto V0 baseline selected or rejected a deployment.

It is not a production-ready public multi-user gateway, a universal model leaderboard, or proof
that automatic routing beats simple baselines. Auto V0 can return `INSUFFICIENT_EVIDENCE`.

## What works in this preview

- OpenAI-style `/v1/models` and `/v1/chat/completions` subset with SSE streaming
- Fastest, Quality, Balanced, experimental Hardware-Aware, and explicit-model modes
- independent local-only, RAM, latency, and availability constraints
- one-model lifecycle manager with stickiness, switching hysteresis, cleanup, and health state
- CPU-first llama.cpp backend, hardware inspection, CLI, Python client, and routing diagnostics
- preserved reproducible research infrastructure from Phases 1–4.5
- provider-independent BYOK cloud access with explicit provider/model selection, streaming,
  typed errors, pricing metadata, and pre-request budgets
- explainable deterministic Auto V0, Economy/Manual policies, dry-run routing, and a zero-cost
  localhost test provider

## Install and try it offline

Python 3.11 and 3.12 are supported.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install "git+https://github.com/Gheubj/AdaptiveAI.git@v0.2.0a1"
adaptiveai --version
```

Alternatively, download `adaptiveai-0.2.0a1-py3-none-any.whl` from the
[GitHub release](https://github.com/Gheubj/AdaptiveAI/releases/tag/v0.2.0a1) and install that exact
file. The fully offline, no-key first run—including Manual, Auto V0, explanations, streaming and
local-only rejection—is in [Developer Preview Quick Start](docs/DEVELOPER_PREVIEW_QUICKSTART.md).

## Quick start

The recommended first run is the zero-cost localhost walkthrough in
[Developer Preview Quick Start](docs/DEVELOPER_PREVIEW_QUICKSTART.md). It uses a public tagged source
checkout because configuration examples are intentionally not installed into the Python package.

Cloud access is opt-in. Copy the provider example from
[`docs/PROVIDER_CONFIGURATION.md`](docs/PROVIDER_CONFIGURATION.md), export your own key, set
`local_only = false`, and use an explicit provider, model, budget, and acknowledgement:

```bash
export MY_PROVIDER_API_KEY='...'
adaptiveai --config adaptiveai.toml providers list
adaptiveai --config adaptiveai.toml chat "Reply with ready" --scope cloud \
  --provider my-provider --model permitted-model --max-estimated-cost 0.01 --allow-paid-cloud
```

Provider inspection, startup, `doctor`, and model discovery do not generate completions. Pricing is
deployment-specific; unknown pricing is never treated as zero. No cloud call is made while
`local_only` is true.

The fully offline Developer Alpha walkthrough is in
[`docs/DEVELOPER_ALPHA_QUICKSTART.md`](docs/DEVELOPER_ALPHA_QUICKSTART.md).

Phase 7.1 externally verified exactly one basic non-streaming ProxyAPI completion. That narrow check
does not validate external streaming, tools, concurrency, reliability, savings, or broad provider
compatibility. See the [provider matrix](docs/PROVIDER_COMPATIBILITY_MATRIX.md).

```bash
curl http://127.0.0.1:8088/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"auto","routing_mode":"balanced","messages":[{"role":"user","content":"Reply with ready"}]}'
```

```python
from adaptiveai.client import AdaptiveAIClient

response = AdaptiveAIClient().chat("Reply with ready", routing_mode="fastest")
print(response["choices"][0]["message"]["content"])
print(response["routing"])
```

## Routing modes

- **Fastest:** lowest profiled p95 latency among eligible models.
- **Quality:** highest available validation quality estimate; errors if none exists.
- **Balanced:** maximizes `quality - latency_weight × predicted_p95_latency`.
- **Hardware-Aware:** experimental quality selection after privacy, RAM, latency, and availability
  constraints.
- **Auto V0:** compatible category evidence after hard eligibility, otherwise explicit abstention or
  configured default; not a learned or validated router.
- **Economy:** lowest known estimated cost among eligible deployments.
- **Manual:** explicit deployment validated against the same hard constraints.

Explicit `model=<id>` bypasses routing but never hard feasibility constraints. Profiles are
host/workload specific. Unknown values remain unknown; AdaptiveAI does not invent quality scores.

## Hardware and privacy

The included research configuration was measured on a 6-core CPU with about 16 GB RAM. Other CPU
hardware must be profiled separately. The server binds only to loopback, cloud inference is
disabled, and default logs do not store prompts or responses.

## Research status

Results below use different panels and must not be merged:

- Phase 2 proprietary-8 TF-IDF: 0.6155 ID versus Best Single 0.5994; ARC-AGI OOD reverses to
  0.2525 versus 0.4275.
- Phase 3.5 semantic MLP: 0.6042 ID and 0.4210 ARC-AGI; it does not dominate both controls.
- Revised constrained gating fixes collapse but does not beat constrained TF-IDF.
- Phase 4.5 local V2: Qwen2.5-0.5B 0.172 and SmolLM2-1.7B 0.416 on 250 held-out tasks. Oracle is
  0.424, leaving only 0.008 headroom above SmolLM2. Oracle is not deployable.
- Hardware-aware routing has **not** demonstrated superiority over fixed strongest-model routing.
- OpenRouter compatibility is configuration-audited but live inference remains unvalidated.

See [research results](docs/RESEARCH_RESULTS.md) and [limitations](docs/LIMITATIONS.md).

## Development

```bash
ruff format --check src tests examples
ruff check src tests examples
pytest
python -m build
```

See [CONTRIBUTING.md](docs/CONTRIBUTING.md), [API_REFERENCE.md](docs/API_REFERENCE.md), and
[PRIVACY_AND_SECURITY.md](docs/PRIVACY_AND_SECURITY.md).

## Citation and license

Release metadata is in `CITATION.cff`. Original project code is released under Apache-2.0. Model
weights, llama.cpp, pretrained encoders, and research datasets retain their own licenses.
Restricted raw data and model weights are not included. See
`THIRD_PARTY_NOTICES.md` for the technical license inventory.
