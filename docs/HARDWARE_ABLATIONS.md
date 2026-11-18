# Hardware Ablations

| Model/state | Load p50 | TTFT p50/p95 | Total p50/p95 | Decode tokens/s | Peak RSS |
|---|---:|---:|---:|---:|---:|
| Qwen cold process, 16 tokens | .528 s | .217/.235 s | .234/.252 s* | 118.0 | .527 GB |
| Qwen warm, long 32 tokens | — | .036/.157 s | .526/.651 s | 66.2 | .532 GB |
| SmolLM2 cold process, 16 tokens | 1.704 s | .522/.524 s | .559/.563 s* | 53.7 | 2.271 GB |
| SmolLM2 warm, long 32 tokens | — | .062/.395 s | 1.307/1.694 s | 26.0 | 2.288 GB |

`*` Server load is recorded separately and precedes request latency; cold disk cache was not cleared.
Keeping a model loaded removes .53–1.70 s of process/model initialization. Switching to SmolLM2
therefore costs roughly 1.70 s before the next request, versus .53 s for Qwen.

Observed concurrency two increased throughput from 3.93 to 4.59 requests/s for Qwen and 3.29 to
4.25 for SmolLM2 on 16-token prompts, while per-request latency rose from .253 to .433 s and .304 to
.470 s. A reduced-RAM condition was evaluated only as a routing-constraint simulation: below
2.288 GB SmolLM2 is excluded; below .532 GB neither measured model is feasible. No unsafe memory
pressure was induced.
