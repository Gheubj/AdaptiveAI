# Constrained Gating Analysis

Historical Architecture C trained cross-entropy against a hard argmax target of observed quality
minus a unit penalty on max-normalized cost. That scale made cost comparable to the entire quality
range, converted a constrained problem into brittle classification, and offered no mechanism for
meeting a specified budget. The observed cheap-model collapse is therefore consistent with the
objective; calibration error and hard-target gradients amplify it. No numerical error was found.

The revision optimizes soft expected observed success with a non-negative primal-dual Lagrange
multiplier for mean historical cost. Hard argmax is used only at inference, so a soft/hard mismatch
remains. Budgets were fixed at 25/50/75/100% of train-selected Best Single cost; deterministic
penalties were selected on validation only. The revised gate met every test budget and outperformed
the deterministic selector at 25, 75, and 100%, tying at 50%. Results are exploratory because this
test set was already inspected.
