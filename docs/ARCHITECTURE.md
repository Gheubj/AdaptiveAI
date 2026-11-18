# Architecture

The API validates bounded input into `InferenceRequest`. `RoutingEngine` filters profiles and emits
diagnostics. `ModelManager` applies documented hysteresis, loads one model, and calls llama.cpp.
Responses distinguish predictions, observations, constraints, selection reason, and fallback.

Product modules (`public`, `config`, `product_registry`, `routing_engine`, `lifecycle`, `api`,
`client`, `local_backend`) use core dependencies. Research ingestion, pandas/torch models, and
benchmark runners are optional and lazy CLI imports. Serving never loads benchmark tables. Cloud
support remains a disabled interface/mock.
