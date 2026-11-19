# Phase 6B.5 Report — Routing Data Foundation and Benchmark Fitness

## A. Engineering

Added separate routing-supervision schemas, a reusable bounded adapter contract, synthetic fixture
adapter, matrix/missingness/duplicate/metric audit, deterministic sampling, exact leakage checks,
binary complementarity and Oracle analysis, historical-cost safeguards, and baseline eligibility.

## B. Source audit

xRouteBench is the strongest technical candidate: 245,903 rows, 18 deployments, dense outcomes,
responses, tokens, latency, prices, native train/test, and diverse tasks. Its reviewed card declares
no dataset license, so row-level ingestion is blocked. RoutingCompendium has 133,253 queries across
five benchmarks and 10–112 candidates, but each split inherits different source rights without a
consolidated ledger. It is also blocked. Existing AdaptiveAI data remains local and non-confirmatory.

## C. Dataset statistics

No new external row-level data was ingested. Therefore new empirical query/model/outcome counts,
missingness, revision coverage, overlap, and task distributions are **N/A**, not zero. Public card
metadata is reported only as source-audit evidence. Tests use an explicitly synthetic fixture.

## D–F. Fitness, complementarity, and cost

xRouteBench would support task-, prompt-, cost-, and latency-aware historical routing, but exact
revision and live-deployment transfer remain limited. RoutingCompendium is promising for cross-pool
research but heterogeneous. No external Best Single, Oracle, pairwise, or cost-headroom result is
reported because permission-fit rows were unavailable.

## G–J

Final verification: 98 tests passed and 3 expected opt-in integrations skipped; whole-package
statement coverage is 68%, while new Phase 6B.5 modules have 91–100% focused coverage. Ruff,
formatting, package builds, archive inspection, clean-target imports, and Git diff checks passed.
Focused tests used 48,548 KiB peak RSS and 0.71 seconds wall time.

No dataset API/download request was made and zero external row-level bytes were ingested. Source
documentation was inspected through web research; its transfer volume was not instrumented. Paid
API, training, inference, model download, and GPU cost were zero.

Phase 6C is preregistered but not started. Decision: **BLOCKED BY DATA RIGHTS / DATA QUALITY** pending
an explicit xRouteBench license/permission response or a cleared RoutingCompendium split. Phase 6A
and 6B are local commits `6bedc34` and `6af2021`; Phase 6B.5 remains uncommitted for review. No push,
tag, release, or package publication occurred.
