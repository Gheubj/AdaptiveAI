# Architecture

## External model intelligence (Phase 6B)

The offline evaluation path is `official bounded API -> immutable manifest -> validated evidence ->
identity resolution -> append-only SQLite store -> compatibility groups -> versioned capability
profiles`. Permission evaluation gates local analysis and publication separately. Live data is never
required for ordinary routing, SDK/API operation, or the default test suite. Aggregate agent-system
evidence remains separate from base-model and provider-deployment evidence.

The API validates bounded input into `InferenceRequest`. `RoutingEngine` filters profiles and emits
diagnostics. `ModelManager` applies documented hysteresis, loads one model, and calls llama.cpp.
Responses distinguish predictions, observations, constraints, selection reason, and fallback.

Product modules (`public`, `config`, `product_registry`, `routing_engine`, `lifecycle`, `api`,
`client`, `local_backend`) use core dependencies. Research ingestion, pandas/torch models, and
benchmark runners are optional and lazy CLI imports. Serving never loads benchmark tables. Cloud
support remains a disabled interface/mock.
