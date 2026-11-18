# End-to-End Evaluation

The real pipeline is `query → constraints → model decision → localhost llama.cpp → response`.
Forty-eight matched model requests and four additional fresh routed held-out requests were executed;
no paid or external inference occurred. Failures/timeouts were zero.

| Policy | Strict quality | Mean observed response latency | p95 | Peak model RSS |
|---|---:|---:|---:|---:|
| Fixed/latency/memory fastest (Qwen) | .25 | .321 s | .551 s | .532 GB |
| Fixed strongest (validation: SmolLM2) | .25 | .754 s | 1.414 s | 2.288 GB |
| Quality-only task router | .25 | .598 s | 1.414 s | 2.288 GB |
| TF-IDF quality | .25 | .754 s | 1.414 s | 2.288 GB |
| Hardware-aware | .25 | .754 s | 1.414 s | 2.288 GB |

All policies tie on the eight-query strict endpoint. Therefore hardware-aware routing does not
improve the observed quality-latency frontier: fixed fastest is dominant for this panel. The hardware
policy followed the stronger validation estimate, which did not transfer to test. Four separately
executed routed requests demonstrate real provenance/inference logging; their strict score was zero
because correct factual values were wrapped in prose. This is exploratory engineering evidence, not
a general model ranking.
