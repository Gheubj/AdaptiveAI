# Routing Research Conclusions

AdaptiveAI has learned five defensible things. First, text-based routing can beat Best Single on an
in-distribution matched panel. Second, lexical TF-IDF is an unusually strong and efficient baseline.
Third, sparse and semantic learned representations trade some ID quality for better performance on
the inspected ARC shift, but neither establishes general OOD superiority. Fourth, standard shared
model embeddings add no consistent benefit. Fifth, cost optimization must be evaluated at matched
budgets: a principled gate fixes Architecture C's collapse, yet constrained TF-IDF remains at least
as compelling.

The scientific contribution is empirical protocol and negative/qualified evidence across quality,
cost, calibration, distribution shift, and compute—not novelty of MiniLM, MLPs, EmbeddingBag, or
Lagrangian optimization. Independent validation is absent because no public dataset combines
independent prompts with the same exact model panel, and paid inference is prohibited.

Recommendation: **GO TO PHASE 4 WITH VALIDATION LIMITATIONS**. Routing software is reproducible and
adequate as a fixed set of baselines for real hardware measurement. Phase 4 must not be presented as
confirmation of general routing superiority. Freeze Best Single, TF-IDF, Sparse A, Semantic MLP,
and deterministic resource-aware controls; treat revised gating as exploratory.
