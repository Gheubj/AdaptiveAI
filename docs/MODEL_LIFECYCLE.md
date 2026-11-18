# Model Lifecycle

Version 0.1.0 keeps at most one llama.cpp model resident and tracks current model, loading, health,
recent requests, last use, and keep-alive. Switching stops the old process before starting a new
one on a dynamic loopback port. Shutdown terminates the child.

Balanced and Hardware-Aware retain an eligible loaded model when predicted benefit is below
`balanced_latency_weight * (candidate_load_seconds + switch_hysteresis_seconds)`. Fastest, Quality,
explicit selection, and hard constraints are not silently overridden. There is no hidden retry:
timeouts and crashes return to the caller to prevent duplicate execution.
