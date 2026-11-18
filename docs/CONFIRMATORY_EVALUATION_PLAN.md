# Independent Confirmatory Evaluation Plan

No result in Phase 3.5 is independent confirmation. RouterBench exposes real prompt/model responses,
performance scores, costs, documented methodology, and a public research implementation, making it
the strongest zero-inference candidate. However, it includes standard families such as MMLU, GSM8K,
MBPP, and MT-Bench, while AdaptiveAI's source archive is itself a routing-benchmark aggregation.
Independence and near-duplicate absence have not yet been established, and matched model identity is
not guaranteed. LLMRouterBench and RouterEval are even more likely to overlap current development
data or lack a comparable proprietary pool.

Before confirmation: acquire a license-pinned snapshot; audit redistribution terms; normalize model
identities; require a complete matched panel; hash and near-duplicate-check prompts against all
26,367 existing queries; freeze one primary endpoint (revised gate versus confidence fallback), one
budget, seed set, and analysis; then evaluate once. If overlap-free coverage is inadequate, report
that independent confirmation remains unavailable rather than manufacturing a holdout.
