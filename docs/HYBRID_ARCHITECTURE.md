# Hybrid Architecture

AdaptiveAI now defines provider-neutral availability, price, privacy, latency, memory, and quality
metadata. `LlamaCppBackend` and `LlamaCppServer` are local providers. `MockCloudProvider` is an
offline test double; no real cloud provider was called. Routing applies `local_only` before model
selection and supports maximum expected cost, p95 latency, RAM, and quality thresholds.

The minimal localhost HTTP layer exposes `/health`, `/v1/models`, `/v1/route`, and an
OpenAI-shaped `/v1/chat/completions`. It rejects public binding by default. Product logging should
store request identifiers, decision provenance, estimates and observations, but prompts only in
explicit research mode. Actual cloud/local claims require a separate paid, consented experiment.
