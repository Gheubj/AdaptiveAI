# Data Quality Report

Source SHA-256: `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`

## Import and integrity

- 548,046 evaluations accepted; 13 quarantined (0.002372%).
- All rejected records contain negative `completion_tokens` (-2 to -56) in GPT-5/OpenRouter HLE
  or SimpleQA files. They were not corrected or clipped.
- 26,367 query IDs and 40 model IDs; primary IDs are unique and foreign keys validate.
- Scores are within [0, 1]; accepted costs and token counts are non-negative.
- 4,327 scores are missing (0.7895%). Of these, 4,326 are the complete `intern-s1-new` SimpleQA
  panel; one is an `internlm3-8b-instruct` MBPP result. Missingness is not random.

## Repeats and costs

There are 10,881 repeated query/model pairs from overlapping HLE `test`/`subset_500` and MMLU-Pro
`test_1000`/`test_3000` releases. Scores conflict in 237 pairs. Preliminary baselines exclude these
pairs rather than selecting a run after observing scores.

384,431 costs are positive and 163,615 are zero. Zero predominantly represents local/lightweight
models and excludes hardware, electricity, load time, and opportunity cost.

## Splits and leakage

The seed-3407 grouped split has 18,184 train, 3,888 validation, 3,895 test, and 400 ARC-AGI OOD-test
queries. Duplicate-group leakage is zero. Detection produced 2,119 exact and 166 conservative near
merges from 12,525 candidates. There are 2,054 non-singleton groups containing 4,339 queries; the
largest group (49) needs manual review before publication freeze.

Most upstream inputs are benchmark evaluation splits. The custom routing split is a split of those
evaluation questions, not evidence that upstream training data were used.
