# Phase 3 Training Protocol

Source SHA-256, duplicate resolution, model pools, and grouped splits are unchanged from Phase 2.
Primary experiments use proprietary-8 because it is the only frozen pool with ARC-AGI coverage.
Previously inspected test/OOD sets are labelled exploratory holdouts; they are never used for early
stopping, calibration, objective, dimension, or cost-lambda selection.

Configuration: five seeds 3407–3411, CPU PyTorch 2.15, AdamW, learning rate 0.003, weight decay
1e-5, batch 128, at most 12 epochs, patience 2, embedding 32, hidden 64, dropout 0.1. Each query is
one batch example containing its complete model label vector. Masked losses average within query
before averaging queries, preventing additional model observations from increasing query weight.
Missing values remain masked.

BCE predicts binary full-success (`score >= 1`). MSE on the fractional upstream score is an
ablation. Temperature scaling is fit only on validation. Checkpoints, seeds, configurations, and
source version are retained under `reports/phase3/proprietary8-main`.

Development-only cross-dataset experiments remove HLE, SimpleQA, or MMLU-Pro from the training
partition and evaluate on the removed train-partition queries. No test or ARC-AGI result selects a
configuration. The fixed architecture was evaluated once on those previously inspected holdouts.
