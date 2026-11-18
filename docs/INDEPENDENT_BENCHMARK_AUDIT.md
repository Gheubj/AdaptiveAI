# Independent Benchmark Audit

Audit date: 2026-11-18, after freezing `PHASE3_6_PREREGISTRATION.md`. No candidate evaluation
labels were downloaded or inspected during this audit.

| Candidate | Provenance / date | Query-level real outcomes | License status | Model compatibility | Prompt overlap risk | Decision |
|---|---|---|---|---|---|---|
| LLMRouterBench | Li et al., released 2026 | Yes; 21+ datasets, 33 models, 400K+ instances | Repository/data terms inherited per constituent source; redistribution remains qualified | Exact proprietary-8 and lightweight-20 | Exact source of AdaptiveAI archive | Ineligible: development data |
| RouterBench | Hu et al., 2024; 30K+ prompts, 11 early LLMs | Yes; responses, costs, correctness | Public repository; dataset card does not establish uniform constituent redistribution rights | Zero exact proprietary-8 versions | High family overlap: MMLU, MBPP, GSM8K, MT-Bench, etc. | Independent provenance but no direct frozen-policy evaluation |
| RouterEval | 2025; 12 evaluations and thousands of open models | Query/model performance records reported | Public research release; verify constituent terms before acquisition | No exact proprietary-8 panel; mostly open models, no comparable API cost | Standard benchmark reuse likely | Ineligible for primary; possible future adaptation study |
| RouteLLM preference data | 2024 | Pairwise preferences, not a complete shared multi-model outcome matrix | Public research code/data | Different two-model/cascade setting | Arena/MT-Bench exposure | Incompatible scoring/panel |
| RouterArena | evolving public framework | Evaluation framework and leaderboard; per-router pools can differ | Apache-2.0 code | No frozen exact eight-model matrix established | Dataset reuse varies | Ineligible for paired primary endpoint |

The local `b79f8c...` archive is the official LLMRouterBench release, so it cannot provide an
independent holdout regardless of a newly created split. Its exact and near-duplicate analysis is
already embodied in grouped splits. RouterBench is genuinely earlier and independently collected,
but its model generation predates all eight exact proprietary candidates. Because direct policy
outputs have eight fixed heads, zero exact model overlap is a terminal compatibility failure. A
prompt overlap download would not change that conclusion and would be an unnecessary archive
acquisition; therefore exact/near-duplicate matching was not run against its labels.

No audited candidate meets all preregistered requirements: independent provenance, ≥500 screened
queries, and the same complete eight-model version panel. Re-running those models would require
paid APIs and some versions may no longer be available. Paid budget is zero. Consequently no
confirmatory evaluation was conducted, no p-value or confirmatory interval is reported, and no
adapted new-pool router is mislabeled as a frozen policy.

Primary sources: [LLMRouterBench repository](https://github.com/ynulihao/LLMRouterBench),
[RouterBench paper](https://arxiv.org/abs/2403.12031),
[RouterBench dataset card](https://huggingface.co/datasets/withmartian/routerbench), and
[RouterEval paper](https://aclanthology.org/2025.findings-emnlp.208/).
