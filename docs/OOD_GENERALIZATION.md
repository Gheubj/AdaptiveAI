# OOD and Cross-Dataset Generalization

ARC-AGI was not used for model selection. Mean five-seed success is 0.3600 for Sparse A, 0.3095 for
Shared B, 0.1295 for Trainable Gate C, and 0.2240 for the deterministic constrained selector.
Phase 2 TF-IDF is 0.2525 and Best Single is 0.4275. Relative to TF-IDF, paired group-bootstrap
differences are +0.1075 [0.0750, 0.1410] for A and +0.0570 [0.0280, 0.0860] for B. Neither reaches
Best Single. C is worse than TF-IDF by -0.1230 [-0.1650, -0.0825].

Train-only leave-dataset-out diagnostics:

| Held-out train dataset | Sparse A | Shared B |
|---|---:|---:|
| HLE | 0.2056 | 0.2063 |
| SimpleQA | 0.5338 | 0.4273 |
| MMLU-Pro | 0.8566 | 0.8580 |

The shared model embeddings do not consistently improve transfer. Sparse A reduces the extreme
lexical TF-IDF failure on ARC-AGI, but high OOD ECE and failure to beat Best Single show that the
distribution-shift problem is unresolved. The hashed lexical encoder may still learn source style;
no semantic-pretrained encoder was downloaded, so semantic-vs-lexical conclusions remain limited.
