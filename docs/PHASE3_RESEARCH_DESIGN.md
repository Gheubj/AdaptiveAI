# Phase 3 Research Design

## Candidate 1: sparse linear multi-model predictor

PyTorch embedding-bag over word/character n-grams with one success head per model. Low complexity,
CPU-friendly, and a direct controlled comparison to TF-IDF logistic. Risk: the same benchmark-style
shortcuts. Needs only the current matrix and grouped splits.

## Candidate 2: small shared text encoder with model embeddings

A compact trainable encoder produces a query vector; learned model embeddings and a bilinear/MLP
head predict success and uncertainty. Medium complexity and memory; supports new model attributes
and shared statistical strength. Risks are overfitting, calibration failure, and sparse model panels.
Compare against TF-IDF, Best Single, and parameter-matched linear heads.

## Candidate 3: constrained mixture-of-experts router

A small gating network predicts per-model success and expected cost, then solves a differentiable
Lagrangian or calibrated budget rule. Medium/high complexity, still laptop-scale with sparse batches.
Potential advantage is explicit quality-cost control; risks include unstable constraint calibration
and learning from historically confounded prices. Requires train-only cost estimates and a separate
hardware dataset before any hardware-aware extension.

Phase 3 should start with Candidate 1 and 2, retain ARC-AGI/leave-one-dataset-out checks, and treat
Candidate 3 as secondary. A Transformer is not presumed superior.
