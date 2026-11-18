# Phase 4 Execution Plan

This is an executable design, not a Phase 4 implementation. No LLM weights were downloaded.

## Initial CPU pool

Use revision-pinned GGUF quantizations only after storage/RAM checks: Qwen2.5-0.5B-Instruct
(Apache-2.0), SmolLM2-1.7B-Instruct (Apache-2.0), and Phi-3.5-mini-instruct 3.8B (MIT). Start with
Q4_K_M and a common 2,048-token context. These sizes give a meaningful capability/RAM ladder on a
16 GB host while leaving memory for the OS, router, and KV cache. Exact GGUF publisher, revision,
hash, tokenizer/template, and quantization must be audited before download. Do not assume the three
models share scoring behavior or safety properties.

## Measurement harness

Use one pinned `llama.cpp` build and record CPU model, cores, RAM, OS, governor, thread count, NUMA,
context, batch, prompt length, output cap, and sampling. For each model measure: cold process launch
and first token; warm time-to-first-token; prompt and generation tokens/s; RSS peak; load/unload and
model-switch time; one and multiple concurrent requests; failure/OOM; and idle/active power only if
RAPL or a calibrated external meter is available. Never report estimated energy as measured.

Run randomized blocks across models with ≥30 warm repetitions and ≥10 true cold repetitions.
Separate router latency, model load, prompt processing, token generation, and queueing. Preserve raw
monotonic timestamps and `/metrics` output. Avoid destructive page-cache clearing; if cold-cache
experiments require privileged cache control, preregister and request explicit approval.

## Baselines and endpoints

Baselines: Best Single, frozen TF-IDF, frozen Semantic MLP, latency-aware deterministic selection,
and a hard RAM/latency-constrained selector. Primary systems endpoint is task success under a fixed
p95 latency and RAM constraint; secondary endpoints are quality, TTFT, tokens/s, throughput, switch
penalty, and measured joules per successful response where available. Train resource policies on a
development measurement block and evaluate once on a held-out temporal block. Simulations may be
used for debugging but must be labeled simulated.

Entry checklist: verify licenses and hashes; reserve disk; pin build/container; validate scoring on
20 smoke prompts; establish thermal stabilization; freeze prompts and randomization; then acquire
real measurements. Abort on repeated OOM, thermal throttling, scorer mismatch, or unresolved model
identity. The first milestone is a reproducible measurement matrix, not a new neural router.

Primary sources for candidate properties are the official
[Qwen model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct),
[SmolLM2 model card](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct), and
[Phi-3.5 model card](https://huggingface.co/microsoft/Phi-3.5-mini-instruct). The harness can use
the official [llama.cpp server metrics](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
