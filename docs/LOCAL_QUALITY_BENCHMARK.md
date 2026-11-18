# Local Quality Benchmark

The original Apache-2.0 micro-panel contains 24 objective prompts: two each of arithmetic, factual
QA, extraction, and exact instruction following in train, validation, and held-out test. The panel
was written and persisted before model execution; all models received identical prompts, temperature
0, seed 3407, and at most 32 output tokens. There are no exact duplicate prompts.

Primary scoring was preregistered strict normalized exact match. Both models scored 2/8 = 0.25 on
test (bootstrap uncertainty is necessarily wide). Qwen scored .25/.00/.25 on train/validation/test;
SmolLM2 scored .25/.375/.25. After outputs were inspected, an explicitly post-hoc answer-containment
diagnostic gave Qwen .875 and SmolLM2 .750 on test. It shows that strict failures often reflect
extra prose, but it cannot replace the frozen endpoint. The 24-query panel is too small for a neural
hardware router; no such model was forced.

Raw outputs, including failures, are preserved in `reports/phase4/local_quality_outputs.parquet`.
