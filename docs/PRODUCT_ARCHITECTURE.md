# Product Architecture

AdaptiveAI 0.1.0 exposes stable experimental dataclasses/protocols for requests, responses,
providers, routing policies, constraints, and diagnostics. Validated TOML feeds a model registry and
profile table. The routing engine is pure pre-inference selection. A one-resident-model manager owns
the llama.cpp process, hysteresis, health, and cleanup. The API and Python client are thin adapters.
Hardware discovery and privacy constraints remain independent of routing mode.

Research modules and dependencies are optional and lazily imported. The built wheel contains code
only; basic serving does not read large benchmark tables. The only implemented real provider is
local llama.cpp. Cloud remains disabled and cannot be reached in local-only mode.
