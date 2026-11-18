# Real Data Schema Audit

Verified: 2026-11-18
Source SHA-256: `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`

The complete 1,283,503,080-byte archive was scanned through `tarfile`; all members passed path,
absolute-path, symlink, and hard-link safety checks. All 700 JSON files parsed successfully.

## Observed layout

The documented `results/bench/<dataset>/<split>/<model>/<timestamp>.json` layout is not the
distributed layout. Two real forms occur:

- `bench-release/<dataset>/<model>/<timestamp>.json`
- `bench-release/<dataset>/<split>/<model>/<timestamp>.json`

This discrepancy initially caused all paths to be rejected and prompted a backward-compatible
parser fix. Dataset/model/split also occur in top-level fields and the source split is preserved.

## Scope and variation

- 700 files, 548,059 source records, 27 datasets, 40 model IDs, and 8 split labels.
- `time_taken` is float in 685 files and integer in 15; it remains aggregate run time.
- `data_fingerprint` is absent in 212 files and `demo` in 65.
- `ground_truth`: 405,854 strings, 20,800 lists, 121,405 nulls.
- `prediction`: 486,911 strings, 57,800 lists, 3,348 nulls.
- `raw_output`: 544,723 strings and 3,336 lists.
- `score`: 543,732 floats and 4,327 nulls.
- `extra_fields` occurs as an object in 11,668 records; `instance_id` occurs in 7,500.

Observed scores are 0, 0.5, and 1, but evaluator semantics differ. They are not treated as one
globally comparable metric. Missing values remain null. Full evidence is stored in
`reports/real_data/schema_audit.json`.
