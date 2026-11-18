# Phase 5 Report — Open-Source MVP

Phase 5 converted the research prototype into a local-first 0.1.0 release candidate. New components
are validated configuration, public types, model registry, four routing modes, explicit selection,
lifecycle manager, OpenAI-style API subset, SSE, client, product CLI, examples, CI, packaging, and
release/security documentation. Research modules were preserved and made optional at installation.

Real smoke-tests used existing weights: doctor passed; CLI Fastest returned a parsed response with
diagnostics; CLI streaming returned content; a temporary AdaptiveAI server passed health, two-model
listing, non-streaming `ready`, streaming chunks/final routing, and process cleanup. Dynamic internal
ports were added after a real fixed-port collision. No benchmark, cloud call, or new model download
was performed.

Final gate: 75 tests passed and one optional real-archive test skipped; this includes a real local
llama.cpp test. Phase-scoped statement coverage was 75%; the subsequent release gate measured 57%
across the whole research-plus-product package. Ruff formatting/lint, dataset validation, JSONL parsing,
wheel integrity, sdist exclusions, and diff checks pass. A fully isolated wheel installation reports
no broken requirements. The final wheel is about 86 KB and sdist about 146 KB.

The release remains experimental: local only, one resident model, bounded concurrency, no auth/TLS,
and no superiority claim. Publication is blocked pending owner approval, canonical license review,
third-party notices, and first-commit staged/history audit. No package or repository was published.
