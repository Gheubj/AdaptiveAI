# Architecture

## External model intelligence (Phase 6B)

The offline evaluation path is `official bounded API -> immutable manifest -> validated evidence ->
identity resolution -> append-only SQLite store -> compatibility groups -> versioned capability
profiles`. Permission evaluation gates local analysis and publication separately. Live data is never
required for ordinary routing, SDK/API operation, or the default test suite. Aggregate agent-system
evidence remains separate from base-model and provider-deployment evidence.

## Routing supervision (Phase 6B.5)

Routing supervision is a separate data plane from aggregate capability evidence. Immutable queries,
historical candidates, and matched outcomes form an explicit sparse matrix with native metric and
split semantics. Adapters are bounded and permission-bearing. Analysis refuses mixed metrics,
conflicts, missing historical prices, and unreviewed historical-to-live identity transfer. Router
training remains a later, separately gated phase.

The API validates bounded input into `InferenceRequest`. `RoutingEngine` filters profiles and emits
diagnostics. `ModelManager` applies documented hysteresis, loads one model, and calls llama.cpp.
Responses distinguish predictions, observations, constraints, selection reason, and fallback.

Product modules (`public`, `config`, `product_registry`, `routing_engine`, `lifecycle`, `api`,
`client`, `local_backend`) use core dependencies. Research ingestion, pandas/torch models, and
benchmark runners are optional and lazy CLI imports. Serving never loads benchmark tables. Cloud
support remains a disabled interface/mock.
