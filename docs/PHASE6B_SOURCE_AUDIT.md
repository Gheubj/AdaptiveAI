# Phase 6B Source Audit

Audit date: 2026-11-18. This is a conservative engineering permission assessment, not legal advice.

## Selected source

- Source: `SWE-bench/SWE-bench_Verified` leaderboard on Hugging Face Hub.
- Maintainers: SWE-bench benchmark team; the interface is maintained by Hugging Face.
- Official interface: `GET /api/datasets/SWE-bench/SWE-bench_Verified/leaderboard` and
  `HfApi.get_dataset_leaderboard()`.
- Documentation: [HF leaderboard data guide](https://huggingface.co/docs/hub/leaderboard-data-guide),
  [HF API reference](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api), and
  [SWE-bench Verified](https://www.swebench.com/verified).
- Format: JSON list with rank, source model ID, aggregate value, verification flag, source URL,
  submission filename, and optional pull request.
- Coverage observed: 78 source rows, 68 distinct source model IDs; metric is `% Resolved` on 500
  human-verified issue-resolution tasks.
- Update frequency: event-driven and not guaranteed by the API contract. Snapshots must be hashed.

## Method and semantics

The score is the percentage of SWE-bench Verified task instances resolved. Leaderboard entries may
describe an entire coding agent, scaffold, tools, prompting, review, and model combination. Phase 6B
therefore records `system_kind=routed_system`; it does not transfer the score to a base model.

## Permission findings

The official HF guide explicitly documents programmatic retrieval for analysis and tooling. The
SWE-bench code package is MIT-licensed, but that code license does not automatically license
leaderboard records, submitted outputs, trajectories, source-repository content, or benchmark
questions. No clear standalone redistribution grant for this API response was found during review.

Decision:

- API metadata access: allowed by documented public interface;
- local ingestion/cache/analysis and derived internal counts: allowed;
- attribution: required conservatively (Hugging Face and SWE-bench);
- commercial use: unknown for the aggregate response;
- raw or normalized record redistribution/publication: **denied while unknown**;
- benchmark tasks, outputs, logs, trajectories: not downloaded or ingested.

The local snapshot is ignored by Git and excluded from packages. Only source descriptions, schema,
code, synthetic fixtures, and non-record operational counts may be committed.
