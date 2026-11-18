# Hardware-Aware Routing

The implementation separates quality estimates, p95 latency estimates, memory feasibility, provider
availability, privacy, and constrained selection. For eligible model set
`E={m: available ∧ privacy ∧ RAM_m≤RAM_available ∧ L95_m≤budget ∧ cost_m≤budget}`, the default policy
selects `argmax(m∈E) predicted_quality(m)` with latency tie-breaking. Latency priority selects the
minimum predicted latency. Every decision stores eligible models, estimates, constraints, provider,
and loaded state; no response-derived feature enters selection.

Implemented policies: fixed fastest, fixed strongest, seeded random, task/quality-only, TF-IDF
quality, latency-aware, memory-aware, and deterministic hardware-aware. A neural hardware policy was
not trained because only 16 development prompts and two arms exist. Local-only filtering occurs
before optimization. Mock cloud support tests the abstraction without network or credentials.
