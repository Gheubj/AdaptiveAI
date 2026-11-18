# Routing Modes

Fastest minimizes profiled p95 latency. Quality maximizes a validation-defined estimate and fails if
estimates are absent. Balanced maximizes `q_hat - weight * latency_p95_hat`; it is a transparent
heuristic, not a universal optimum. Hardware-Aware filters by availability, privacy, RAM, and
latency, then selects quality; it is experimental.

`local_only` applies to every mode. Explicit selection bypasses the objective but not hard
constraints. Diagnostics distinguish predictions from observations. Missing values are null, never
zero. Profiles are specific to their host and validation workload.
