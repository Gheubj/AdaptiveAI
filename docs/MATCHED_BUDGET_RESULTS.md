# Matched-Budget Results

The audit re-evaluated 1,987 identical proprietary-8 test queries with the same historical costs.
Budgets remained 25/50/75/100% of train-selected Best Single cost. Penalties were chosen on
validation only; revised gates were reproduced from the frozen implementation and seed 3407.

| Method | 25% quality / cost | 50% quality / cost | 75% quality / cost | 100% quality / cost |
|---|---:|---:|---:|---:|
| Revised gate | .5778 / .01485 | .5873 / .02711 | .6029 / .03975 | .6130 / .04783 |
| Deterministic semantic selector | .5732 / .01481 | .5873 / .03032 | .5888 / .03321 | .5888 / .03321 |
| Validation-constrained TF-IDF | .5642 / .00684 | **.6034 / .02547** | **.6155 / .03906** | **.6155 / .03906** |
| Original deterministic selector | .5511 / .00130 | .5511 / .00130 | .5511 / .00130 | .5511 / .00130 |
| Original trainable gate | .4348 / .00102 | .4348 / .00102 | .4348 / .00102 | .4348 / .00102 |
| Cheapest | .4212 / .00119 | .4212 / .00119 | .4212 / .00119 | .4212 / .00119 |
| Best Single | .5994 / .06049* | .5994 / .06049* | .5994 / .06049* | .5994 / .06049 |

`*` violates the target mean budget. Every constrained method met all four mean budgets.

Revised-minus-deterministic paired differences were +.0045 [−.0091, .0181], .0000
[−.0136, .0131], +.0141 [.0010, .0272], and +.0242 [.0116, .0367]. Thus revised gating measurably
beats its semantic deterministic control at 75% and 100% in this repeated exploratory test. It does
not dominate constrained TF-IDF: TF-IDF is higher quality and slightly cheaper at both upper
budgets. Original Architecture C is confirmed to be a cheap-model collapse, not a Pareto winner.

Per-query decisions, selection shares, 10,000-draw paired intervals, histories, and the Pareto plot
are in `reports/phase3_6`. These intervals are not independent confirmation and do not justify
test-selected deployment.

The matched-budget Pareto figure is a generated local research artifact and is intentionally not
included in the public source repository.
