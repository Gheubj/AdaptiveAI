# Error and Shortcut Analysis

TF-IDF's avoidable-failure rate is 19.71% on lightweight test and 17.41% on proprietary test. Its
weakest lightweight tasks are ArenaHard coding (0.119), ArenaHard math (0.148), and ArenaHard
general (0.228); strongest include AIME (1.000, only five test queries), MATH500 (0.960), and ARC-C
(0.934). Proprietary weaknesses are HLE (0.181), SWE-bench (0.379), and tau2 (0.414).

The Oracle gaps are 0.1971 (lightweight) and 0.1741 (proprietary), leaving substantial headroom.
Best Single beats TF-IDF decisively on ARC-AGI OOD: 0.4275 versus 0.2525. Thus text routing gains do
not transfer automatically to a new task family.

TF-IDF can learn benchmark style, boilerplate, language, and formatting rather than transferable
competence. The metadata-assisted baseline has direct benchmark-category information and is not
deployable evidence. ARC-AGI failure is the strongest current shortcut warning. Future work must
include source-adversarial validation, leave-one-dataset-out evaluation, lexical-ablation tests, and
human-defined task features. Negative findings are retained.
