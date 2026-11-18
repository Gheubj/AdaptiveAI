# License Audit

Verified: 2026-11-17

## LLMRouterBench project and result archive

Primary evidence: [LLMRouterBench GitHub issue #5](https://github.com/ynulihao/LLMRouterBench/issues/5),
owner response dated 2026-08-26.

The repository owner states that MIT is intended for the top-level source code and that benchmark
data in `bench-release.tar.gz` may be used for **non-commercial academic research and reproduction
of research results**. This is a purpose-limited permission, not evidence that the archive may be
freely redistributed or commercially reused. The owner also said corresponding license files and
the Hugging Face card would be updated.

The Hugging Face repository was checked on 2026-11-17 and now contains an MIT `LICENSE`. Its scope
clause applies MIT to original code and benchmark-data contributions only to the extent of the
contributors' rights, while third-party materials retain their original licenses. Because issue #5
states a narrower data permission, this project conservatively relies on the explicit
non-commercial academic/reproduction permission for the archive.

Operational policy:

- Keep raw records and the archive out of Git.
- Use them only for non-commercial academic research and result reproduction.
- Publish code, configurations, lineage manifests, and permissible aggregate statistics by default.
- Do not infer permission to redistribute prompts, ground truths, or model outputs.

## Constituent datasets

The archive combines multiple benchmarks, each potentially subject to its own license, terms,
attribution requirements, and model-output restrictions. Archive-level permission cannot waive
third-party rights. A dataset-by-dataset table will be finalized from the datasets observed in the
real archive. Until primary license evidence is recorded, each constituent license remains
`unresolved` and raw redistribution remains prohibited.

| Component | Status | Note |
|---|---|---|
| MMLU-Pro | verified MIT | The benchmark paper documents its component licenses. |
| HumanEval | verified MIT | Official OpenAI HumanEval repository license. |
| GPQA | restricted/non-commercial evidence | Exact archive-variant terms need confirmation. |
| AIME | unresolved | Competition problem rights are not established by archive permission. |
| MATH-500, MATHBench, LiveMathBench | partially traced | Confirm version-specific derived-source terms. |
| MBPP, LiveCodeBench, SWE-bench | partially traced | Incorporated task/repository licenses vary. |
| HLE, SimpleQA, ArenaHard variants | unresolved | Source questions and judge-output terms need review. |
| ARC-AGI, ARC-C, BBH, K&K, KORBench, Winogrande | unresolved | Record primary version evidence before redistribution. |
| FinQA, MedQA | unresolved/sensitive | Underlying financial/medical content may add restrictions. |
| EmoryNLP, MELD | unresolved | Dialogue-source rights may differ from benchmark code. |
| tau2 | partially traced | Project is permissive; bundled domain content needs review. |

This supports local non-commercial analysis under the archive permission, not republication of raw
constituent records.

## OpenRouter catalog

Only public, read-only catalog metadata are collected. No generated answers or paid inference are
requested. Snapshot metadata retain retrieval time and raw API fields; downstream publication must
follow OpenRouter's then-current terms.
