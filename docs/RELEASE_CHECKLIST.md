# Release Checklist — 0.1.0 RC

## Completed

- Core editable install and wheel metadata; clean-wheel import/CLI smoke-test.
- Wheel and sdist build; restricted/cache directories excluded from both release artifacts.
- Doctor, hardware, model listing, direct chat, server, Python client, and examples.
- Fastest, Quality, Balanced, experimental Hardware-Aware, explicit selection, and local-only.
- Non-streaming and SSE streaming API with validation, size/concurrency bounds, structured errors.
- Lifecycle health, hysteresis, dynamic ports, timeout/crash errors, shutdown, and no hidden retry.
- Offline tests, localhost integrations, real local CLI/API smoke-tests, lint, format, and CI file.
- README, API/config/privacy/research/limitations documentation and audit.
- Canonical Apache-2.0 text and a third-party technical notice inventory.
- Explicit staged-file allowlist, generated manifest, security/privacy scan, and staged-snapshot
  build/install validation.

## Blocking before publication

- Owner must approve Apache-2.0 selection, copyright/attribution text, and third-party notices.
- Owner must approve the exact first commit/repository contents and public destination.
- After owner-authorized initial commit, scan the resulting history before any push.

## Nonblocking experimental limitations

- No production authentication/TLS, multi-model residency, GPU validation, or cloud provider.
- One-process development server and limited OpenAI compatibility.
- No demonstrated routing superiority over Fixed Strongest; profiles are host/workload specific.
- Dynamic port allocation has a small bind race; cancellation has no backend acknowledgement.

## Manual approval

Do not upload to GitHub, PyPI, an artifact registry, or create a release/tag without explicit owner
approval. Model weights and restricted datasets are never release assets.
