# Statistical Analysis

All intervals are 95% cluster-bootstrap intervals. The resampling unit is the duplicate group,
stratified by dataset for marginal success estimates. Primary runs use 1,000 replicates; paired
TF-IDF versus Best Single differences use 5,000 replicates on identical queries. Random reports five
fixed seeds.

On lightweight-20 test (2,334 queries), TF-IDF minus Best Single is +0.0231 with paired CI
[+0.0090, +0.0377]. On proprietary-8 test (1,987), it is +0.0161 [+0.0020, +0.0302]. However,
proprietary validation is -0.0010 [-0.0155, +0.0140], and proprietary ARC-AGI OOD is -0.1750
[-0.2250, -0.1250]. These are interval estimates, not a universal significance claim. Multiple
datasets, policies, and comparisons were inspected; no multiplicity-adjusted confirmatory test was
pre-registered.
