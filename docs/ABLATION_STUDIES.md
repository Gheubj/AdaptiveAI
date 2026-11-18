# Ablation Studies

All ablations use seed 3407 and validation only.

| Architecture | Objective | Dim | Validation success |
|---|---|---:|---:|
| Sparse | BCE | 16 | 0.5699 |
| Shared | BCE | 16 | 0.5559 |
| Sparse | MSE | 16 | 0.5764 |
| Shared | MSE | 16 | 0.5684 |
| Sparse | BCE | 64 | **0.5794** |
| Shared | BCE | 64 | 0.5614 |
| Sparse | MSE | 64 | 0.5769 |
| Shared | MSE | 64 | 0.5574 |

Explicit model embeddings consistently trail the independent output-head architecture in this
budget. MSE can help at dimension 16 but not consistently. Temperature scaling improves calibration
without changing argmax routes. Cost-aware trainable gating is substantially worse than deterministic
selection using the same predictions, so learned gate complexity is not justified by these results.

The main 32-dimensional configuration was frozen before these ablations and was not replaced after
test inspection. Results are exploratory and uncorrected for multiple comparisons.
