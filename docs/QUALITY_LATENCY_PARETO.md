# Quality–Latency Pareto Analysis

On offline matched observations, Fixed Fastest is the low-latency/low-memory endpoint and Task-Aware
is the measured high-quality endpoint: it matches Fixed Strongest quality while reducing median and
p95 response latency. Fixed Strongest, TF-IDF, Semantic, and unconstrained Hardware-Aware are
dominated offline by Task-Aware. Oracle is an unattainable diagnostic bound.

The offline Task-Aware advantage does not survive a naïve single-loaded-model lifecycle. Because
queries alternate task families, 16 real switches make it slower than persistent Fixed Strongest.
A scheduler with model residency, batching, or switch hysteresis would be required before calling
Task-Aware a superior end-to-end Pareto point. RAM constraints below the measured 2.288 GB exclude
SmolLM2 and force Qwen; this is a simulated constraint decision, not induced memory pressure.

Hardware-aware routing therefore provides correct feasibility behavior but no demonstrated quality
gain over Fixed Strongest. Its limitations are insufficient complementary capacity, predictors that
rationally choose the dominant model, optimistic tail-latency prediction, and switching overhead.
