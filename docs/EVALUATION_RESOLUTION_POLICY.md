# Evaluation Resolution Policy

## Observed conditions

The archive contains 10,881 repeated query/model pairs. Of these, 10,644 have the same score across
overlapping releases and 237 have conflicting scores. Full raw outputs were deliberately not loaded
for classification because they are large and are unnecessary for routing; consequently the 10,644
are conservatively called `repeated_release_same_score_output_uninspected`, not proven bit-identical
or independent stochastic generations. There are 4,327 missing scores, which remain null.

## Primary policy

The primary evaluation matrix uses the arithmetic mean of observed repeated scores and costs for a
query/model pair. This treats repeated observations as estimates for one query/model cell, never as
independent queries. It is deterministic, retains provenance in the immutable source table, and
does not select the most favorable run. Missing values are ignored only within an otherwise observed
cell and are never replaced with zero; a cell with no observed score is unavailable.

Sensitivity policies are: (1) deterministic first record ordered by source member and record index,
and (2) exclusion of every repeated pair. On proprietary-8 test, TF-IDF success is 0.6155 under mean,
0.6165 under representative, and 0.6237 under exclusion; Best Single is 0.5994, 0.5994, and 0.6102.
The direction is stable, but absolute results and Oracle coverage change, so the primary policy must
be reported with sensitivity results.

`repeat_classification.parquet` stores pair-level provenance classification. The normalized source
rows are never rewritten.
