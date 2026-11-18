# External Evidence Quality

The pilot evidence has complete source URL/record ID provenance and preserves the original percent
score. It is limited by unknown model revisions, unknown scaffold/harness revisions, missing
sampling/prompt configuration, aggregate-only results, source self-reporting, possible benchmark
contamination, and incomplete leaderboard coverage.

At retrieval, every accepted HF row had `verified=false`; AdaptiveAI labels them `declared`, not
independently verified. Aggregate `% Resolved` is not a per-prompt success probability and does not
support statistical significance claims without per-instance paired outcomes. Two records are
comparable only when benchmark/version, population, metric/unit/scale, harness configuration,
revision semantics, and system kind match.

The imported evidence can support source discovery, coverage assessment, and cautious candidate
screening. It cannot establish general coding quality, base-model quality, a universal rank, or a
prompt-aware routing improvement.
