# Compute Budget Comparison

| Method | Fitted parameters | Mean training time | Online representation |
|---|---:|---:|---|
| Semantic Logistic | 3,080 | 0.2 s | MiniLM |
| Semantic MLP | 25,160 | 0.7 s | MiniLM |
| Semantic Shared | 18,849 | 0.8 s | MiniLM |
| Hybrid | approx. 240,000 coefficients | 13.2 s | TF-IDF + MiniLM |

MiniLM preprocessing took 460.2 s and the cache is 37 MB. Full encoder latency, including the
representation rather than head-only routing, was 10.35 ms for a single query and 272.97 ms for a
batch of 128 (2.13 ms/query). Head training and inference are negligible relative to encoding.
These CPU measurements are not end-model inference latency and do not establish hardware-aware
routing benefits.
