# Routing Data Leakage Audit

The audit preserves source splits and assigns explicit roles: train, validation, exploratory test,
or untouched confirmatory test. It detects repeated query IDs and exact normalized-text hashes across
splits. Semantic, translated, paraphrased, benchmark-training, and upstream model-training overlap
may remain and are documented as uncertainty.

No external row-level source was downloaded, so no new cross-source overlap measurement exists.
Existing LLMRouterBench test and ARC-AGI outcomes were repeatedly inspected during earlier phases and
remain exploratory. Phase 4.5 local queries also remain previously inspected. Neither can become a
new independent confirmation set by relabeling.

Future admission requires source lineage, stable group hashes, duplicate/near-duplicate grouping,
and a confirmatory split frozen before model or policy selection.
