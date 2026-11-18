# Paper Dataset Reconciliation

## Evidence and result

The ACL 2026 paper freezes 391,645 instances, 21 unique datasets, and 33 models in two settings:
15 datasets × 20 lightweight models and 10 datasets × 13 flagship models, with four datasets shared
between settings. The current repository describes `21+` datasets, its evaluator lists `27+`, and
the downloaded archive contains 548,046 accepted rows, 27 datasets, and 40 model identifiers.

Applying the published dataset and model whitelists to the current archive yields 431,776 rows
before repeat resolution, not 391,645. Therefore the exact paper table cannot be reconstructed from
names alone. The remaining difference is consistent with later archive additions/re-runs and
overlapping HLE `test/subset_500` and MMLU-Pro `test_1000/test_3000` releases. No paper comparison
is made as if these setups were interchangeable.

## Frozen subsets

- **Paper-aligned approximation:** the published 21-dataset and 33-model whitelist, explicitly
  labelled approximate; 431,776 archive rows before resolution.
- **Extended archive:** all 548,046 accepted rows, 27 datasets, 40 models; preserved unchanged.
- **Phase 2 quality:** complete lightweight-20 panels, grouped custom splits.
- **Phase 2 cost:** the predeclared proprietary-8 common panel from Phase 1B. This is not the
  paper's 13-model cost pool.

The machine-readable counts and repeat classes are in
`reports/phase2/reconciliation/reconciliation_summary.json`. Exact reconstruction would require a
paper-era file manifest (member names/hashes), which is not published in the available materials.

Primary references: the official paper and official repository/configuration, recorded in
`references/references.bib`.
