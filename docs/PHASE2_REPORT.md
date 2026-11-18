# Phase 2 Report

## Research question and setup

Can pre-inference text or metadata routing beat a train-selected fixed model on matched panels, and
what quality-cost trade-off is available? The source archive, group split, model pools, resolution
policy, and seeds are frozen in `EXPERIMENTAL_PROTOCOL.md`. No paid inference was performed.

## Main test results

| Pool / router | Success | 95% CI | Mean historical USD/query | Gain vs Best | Gap to Oracle |
|---|---:|---:|---:|---:|---:|
| Lightweight Best Single | 0.6547 | [0.6378, 0.6731] | N/A | 0 | 0.2202 |
| Lightweight Task-Aware metadata | 0.6607 | [0.6422, 0.6788] | N/A | +0.0060 | 0.2142 |
| Lightweight TF-IDF logistic | 0.6778 | [0.6593, 0.6947] | N/A | +0.0231 | 0.1971 |
| Lightweight Oracle (post-hoc) | 0.8749 | [0.8606, 0.8880] | N/A | +0.2202 | 0 |
| Proprietary Best Single | 0.5994 | [0.5776, 0.6209] | 0.06049 | 0 | 0.1902 |
| Proprietary Cheapest | 0.4212 | [0.3991, 0.4439] | 0.00119 | -0.1782 | 0.3684 |
| Proprietary TF-IDF logistic | 0.6155 | [0.5948, 0.6366] | 0.03906 | +0.0161 | 0.1741 |
| Proprietary Oracle (post-hoc) | 0.7896 | [0.7725, 0.8072] | 0.00620 | +0.1902 | 0 |

Random success is 0.4970 ± 0.0059 SD (lightweight) and 0.4818 ± 0.0101 (proprietary), across seeds
3407–3411. Validation-selected budget points at 25/50/75/100% of Best Single validation cost obtain
test success 0.5642/0.6034/0.6155/0.6155 and mean cost $0.00685/$0.02547/$0.03906/$0.03906.

On ARC-AGI OOD, proprietary Best Single scores 0.4275 [0.3775, 0.4776], TF-IDF 0.2525
[0.2050, 0.2925], and Oracle 0.5350 [0.4825, 0.5850]. Lightweight OOD is unavailable because none
of its models occurs in the ARC-AGI panel.

## Interpretation and limitations

TF-IDF exceeds Best Single on both final ID tests, but the proprietary validation interval includes
zero and OOD reverses the result. Routing helps within the observed benchmark mixture, particularly
when model complementarity is large; it is not yet robust to task shift. Query n-grams and coarse
task metadata carry signal, but likely include benchmark-source shortcuts. Hardware efficiency is
not evaluated. Costs for local models omit compute, and proprietary costs are historical.

Engineering checks and exact artifacts are recorded under `reports/phase2`. The framework is ready
for a controlled neural-router study, provided Phase 3 treats OOD robustness and shortcut learning
as primary objectives rather than assuming a larger model will win.

Final full runs took 99 s (lightweight, 1.01 GB peak RSS) and 85 s (proprietary, 1.17 GB). A separate
5,000-feature batch probe measured 0.396 ms/query for TF-IDF transform plus eight probability heads;
this is router-only latency and is not selected-LLM latency. The full 30,000-feature configuration
is not assigned this probe value. Phase 1B preprocessing remained 175 s / 1.34 GB.

**GO TO PHASE 3**, with the restrictions above.
