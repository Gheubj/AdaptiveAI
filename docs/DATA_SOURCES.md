# Data Sources and Licensing

## LLMRouterBench

- Repository: https://github.com/ynulihao/LLMRouterBench
- Dataset: https://huggingface.co/datasets/NPULH/LLMRouterBench
- Inspected file listing (2026-11-17): `.gitattributes`, `download.md`, and a 1.28 GB
  `bench-release.tar.gz`.
- Documented record fields include query/prompt, prediction/raw output, ground truth, score, token
  counts, and cost. Expected paths are `results/bench/<dataset>/<split>/<model>/<timestamp>.json`.
- The repository currently describes more than 21 datasets and separate lightweight/performance-cost
  model pools. Per-dataset evaluators differ (accuracy, pass@1, success rate, or LLM judge).

**License status:** the repository owner clarified in GitHub issue #5 on 2026-08-26 that the
top-level code is intended to be MIT licensed and that `bench-release.tar.gz` may be used for
non-commercial academic research and reproduction of research results. This is not treated as
permission for unrestricted archive redistribution. Individual constituent licenses and provider
terms remain unresolved; see `docs/LICENSE_AUDIT.md`.

## OpenRouter model catalog

- Endpoint: `GET https://openrouter.ai/api/v1/models`
- Intended use: timestamped catalog metadata only; no inference requests.
- Captured fields: exact ID, canonical slug, provider prefix, context length, modalities,
  supported parameters, and prompt/completion prices.
- Prices are mutable catalog observations and must always be interpreted with the snapshot time.

## Local synthetic fixtures

Tests generate a tiny archive in a temporary directory. These records exist only to verify code;
they are not evidence, are not included in EDA, and must never enter scientific results.
