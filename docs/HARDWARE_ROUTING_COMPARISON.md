# Hardware Routing Comparison

All offline policy rows use the same 250 queries and the actually observed output of the selected
model. Quality predictors fit only the 150 train rows; model/task choices and TF-IDF regularization
use 100 validation rows. MiniLM is the already pinned local encoder and received no test tuning.

| Policy | Quality | 95% CI | p50 latency | p95 latency | Peak RAM | Violations |
|---|---:|---:|---:|---:|---:|---:|
| Fixed Fastest | .172 | [.128,.220] | .409 s | 1.023 s | .532 GB | 0 |
| Fixed Strongest | .416 | [.356,.480] | .919 s | 1.886 s | 2.288 GB | 57 |
| Task-Aware | .416 | [.356,.480] | .746 s | 1.761 s | 2.288 GB | 15 |
| TF-IDF | .416 | [.356,.480] | .919 s | 1.886 s | 2.288 GB | 57 |
| Semantic MiniLM | .416 | [.356,.480] | .919 s | 1.886 s | 2.288 GB | 57 |
| Hardware-Aware | .416 | [.356,.480] | .919 s | 1.886 s | 2.288 GB | 57 |
| Oracle (post-hoc) | .424 | [.364,.488] | .525 s | 1.760 s | 2.288 GB | 15 |

The declared latency constraint used Phase 4 warm-profile p95 predictions. Violations show that the
short/medium/long calibration workload underpredicts tail latency for V2 response distributions.
Fixed Strongest beats Fastest by .244, paired bootstrap 95% CI [.188,.300], with 63 gains and two
losses (exact McNemar p=1.16e-16). Task-Aware has the same aggregate test quality as Strongest, not a
quality improvement. TF-IDF and Semantic collapse to Strongest because development evidence offers
negligible safe headroom.

In real 24-query execution, Fixed Fastest/Strongest quality was .167/.500. Task-Aware reached .458,
performed 16 switches, spent 24.79 s loading, and had p50/p95 end-to-end-with-load latency
1.598/3.532 s. Fixed Strongest had zero switches and .915/1.896 s. Router computation itself was
1–3 microseconds; lifecycle cost, not router inference, dominates.
