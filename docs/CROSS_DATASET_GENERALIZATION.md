# Cross-Dataset Generalization

Train-only leave-dataset-out folds excluded every held-out dataset's labels from fitting. Eligible
folds had at least 100 complete proprietary-8 queries. Semantic Logistic versus fold-specific Best
Single was: SimpleQA 0.400/0.537, MMLU-Pro 0.847/0.859, HLE 0.165/0.215, LiveCodeBench 0.750/0.792,
ArenaHard 0.719/0.674, SWE-bench 0.330/0.357, ArenaHard-math 0.559/0.565, creative-writing
0.865/0.792, coding 0.725/0.671, tau2 0.510/0.537, and GPQA 0.819/0.854.

The gains cluster in ArenaHard-style domains; broad benchmark-family generalization is not
supported. These are development diagnostics and were not used to select a favorable single fold.
