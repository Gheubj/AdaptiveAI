# Local Model Registry

| ID | Source | Parameters | Quantization | Bytes | License | SHA-256 |
|---|---|---:|---|---:|---|---|
| qwen2.5-0.5b-instruct-q4km | bartowski/Qwen2.5-0.5B-Instruct-GGUF | 0.5B | Q4_K_M | 397,808,192 | Apache-2.0 | `6eb923…8653` |
| smollm2-1.7b-instruct-q4km | bartowski/SmolLM2-1.7B-Instruct-GGUF | 1.7B | Q4_K_M | 1,055,609,824 | Apache-2.0 | `77665e…34d7` |

Total new weights are 1.453 GB, below the 2 GB limit. Both are community GGUF quantizations of the
official Apache-2.0 instruction models. Files were treated as data by pinned llama.cpp; no repository
script or remote code was executed. Operational context was fixed at 2,048 even though model cards
advertise larger maxima. Exact local paths and full hashes are in `data/local_model_registry.json`.
