# Phase 3 Report

## Outcome

All three required PyTorch architectures were implemented and trained on real proprietary-8 panels
with five seeds. Architecture C is a separately trained gating network and was compared directly
with a deterministic constrained selector using the same Architecture B predictions.

| Router | ID quality | Gain vs TF-IDF | Cost/query | OOD quality | CPU p50/p95 ms |
|---|---:|---:|---:|---:|---:|
| Best Single | 0.5994 | -0.0161 | 0.06049 | **0.4275** | N/A |
| TF-IDF | **0.6155** | 0 | 0.03906 | 0.2525 | batch probe 0.396/query |
| Architecture A Sparse | 0.6086 ± 0.0035 | -0.0069 | 0.05094 | 0.3600 ± 0.0677 | 0.057/0.095 |
| Architecture B Shared | 0.5986 ± 0.0072 | -0.0169 | 0.04752 | 0.3095 ± 0.0396 | 0.140/0.226 |
| Architecture C Trainable Gate | 0.4339 ± 0.0052 | -0.1816 | **0.00102** | 0.1295 ± 0.0021 | 0.194/0.369 |
| Deterministic constrained B | 0.5462 ± 0.0035 | -0.0694 | 0.00132 | 0.2240 ± 0.0283 | included in B |
| Oracle, post-hoc | 0.7896 | +0.1741 | 0.00620 | 0.5350 | N/A |

## Interpretation

Neural routing does not outperform TF-IDF on previously inspected ID test. A's paired difference is
-0.0069 with 95% CI [-0.0198, 0.0060]. B is worse and learned model embeddings do not help under the
matched budget. A improves substantially over TF-IDF on ARC-AGI, but remains below Best Single and
has poor OOD calibration. Calibration improves ID Brier/ECE but cannot change argmax routing.

C collapses toward the cheapest model. This is not a software-only selector: it is a trained gate,
but its objective/labels yield a poor quality-cost policy. The deterministic control is materially
better, demonstrating that extra policy learning is harmful here. Cross-dataset results vary sharply,
consistent with dataset-style shortcuts and competence-distribution shift.

## Engineering and validity

Models train locally on CPU, use query-balanced masked losses, preserve missing labels, and never
consume answers, outputs, dataset ID, actual completion cost, test labels, or OOD labels as inputs.
The five-seed suite took 5:47 wall time and 2.05 GB peak RSS. Ablations took 3:01 and 1.80 GB.
Test/OOD were already observed in Phase 2; all Phase 3 results are exploratory, not a fresh
confirmatory test. No multiple-comparison correction or semantic pretrained encoder was used.

All architectures and required analyses exist, but the evidence does not justify beginning a
hardware-aware implementation. More Phase 3 work should preregister a new confirmatory holdout,
improve semantic/OOD representations, and redesign constrained learning.

**NOT READY FOR PHASE 4**
