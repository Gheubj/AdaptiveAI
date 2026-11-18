# Local Benchmark V2

Benchmark V2 is a frozen, locally authored Apache-2.0 panel of 500 unique objective prompts: 150
train, 100 validation, and 250 held-out test. Each split is approximately stratified across
arithmetic, factual QA, JSON extraction, exact instruction following, simple program-output
prediction, and deterministic reasoning. Rows preserve query ID, split, task, reference, answer
type, generator version, and seed. No Phase 4 prompt is reused verbatim.

The panel is generated deterministically by `phase45-v1` with seed 3407. Programming questions ask
for output prediction; model-generated code is never executed. The benefit is reproducibility,
objective scoring, and safe redistribution. The limitation is substantial template regularity and
local authorship: this is a systems validation workload, not a broad natural-language benchmark.
The prior eight-query Phase 4 test remains exploratory and is not included.

Both models were run on every row with their GGUF chat templates, llama.cpp `a300a9c`, six CPU
threads, temperature zero, seed 3407, context 2,048, and maximum 48 generated tokens. The resumable
run recorded 1,000 responses, raw text, normalized answer, correctness, TTFT, latency, token counts,
throughput, load time, and failure status.
