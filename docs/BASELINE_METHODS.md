# Baseline Methods

- Random uniformly selects an allowed model; five seeds 3407–3411 are reported.
- Cheapest uses train-estimated historical request cost only in proprietary-8.
- Best Single is the highest train success model and is fixed before test.
- Task-Aware selects the train-best model for a coarse task class. Because benchmark-derived task
  metadata is supplied, this is explicitly `metadata-assisted`, not a normal deployable policy.
- TF-IDF + Logistic fits one L2-regularized binary success predictor per model from query text. It
  supports multiple successful models naturally and chooses maximum predicted success.
- Cost-Constrained subtracts `lambda × expected train cost` from predicted success. Lambdas
  `{0,1,5,20,100}` are frozen. Budget-grid policies are selected on validation only.
- Oracle sees the observed matrix after inference and chooses maximum score with minimum-cost
  tie-break. It is an upper bound, never a router.

The common evaluation engine records decisions, model distribution, entropy, avoidable failures,
quality, costs and per-dataset results. Actual response tokens/costs are evaluation-only.
