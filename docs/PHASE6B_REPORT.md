# Phase 6B Report — External Benchmark Integration

## A. Engineering

Implemented a bounded Hugging Face SWE-bench Verified adapter, typed network/import errors,
immutable manifests, conservative identity resolution, SQLite evidence history, permission-aware
export, comparable-pair queries, coverage/profile summaries, CLI commands, and offline/live examples.

## B. Benchmark source

The source is the official HF dataset leaderboard API for `SWE-bench/SWE-bench_Verified`. The API is
documented for analysis/tooling. SWE-bench code is MIT, but result redistribution is not clearly
granted by that code license; raw/normalized rows remain local and export-denied. Attribution to HF
and SWE-bench is retained.

## C. Imported data

One bounded adapter request downloaded 59,880 bytes. The API reported 78 rows; the configured pilot
accepted the first 20, rejected 0, covered 20 source IDs, one benchmark, and one original percent
metric. Exact canonical resolutions: 0. Unknown revisions: 20. The import is explicitly incomplete
because of the result bound.

## D. Evidence quality

All 20 records have provenance, but all were `verified=false`, all lack exact revision/scaffold
configuration, and all have unknown redistribution rights. Results describe agentic systems and do
not isolate base-model capability. Only protocol-compatible aggregates may be compared, without a
significance claim.

## E. Developer interface

`adaptiveai intelligence` lists sources/permissions, performs live or offline bounded imports,
queries evidence, and compares two source IDs. `examples/external_evidence.py` demonstrates import,
storage, provenance, unresolved identity, profile creation, and comparison; it is offline by default.

## F. Verification

Final verification passed: 90 tests, 3 expected opt-in skips, 65% whole-package statement coverage,
and 93–98% coverage for the new adapter/store/resolution/comparison/profile modules. Ruff and tracked
source/test/example formatting are clean. Wheel and sdist builds passed; archive inspection found no
planning files, external caches, evidence databases, raw/processed/model data, vendor code, reports,
virtual environments, or caches. A clean target installation imported the new modules and executed
`adaptiveai intelligence sources` successfully.

## G. Resources

Paid API spend, inference calls, and model downloads were zero. Two anonymous metadata requests
were made during development/audit, each 59,880 bytes: one schema inspection and one adapter pilot,
for 119,760 downloaded bytes total. No task dataset, output, trajectory, or weight was downloaded.

## H. Scientific interpretation

The integration proves that real aggregate evidence can pass through provenance, permission,
identity, storage, profile, and comparison boundaries. It does not validate prompt-aware routing,
general coding superiority, a universal model rank, or a per-query probability.

## I. Phase 6C recommendation

Proceed only to a separately authorized Benchmark-Informed Routing Baseline V2 after exact candidate
identity and matched per-instance outcomes are available. Aggregate SWE-bench agent scores alone are
insufficient training or validation labels.

## J. Git status

Phase 6A is preserved as local commit `6bedc34`. Phase 6B remains local and unpublished on
`codex/phase6a`; `planning/` and real evidence caches are excluded. No push, tag, release, or package
publication was performed.
