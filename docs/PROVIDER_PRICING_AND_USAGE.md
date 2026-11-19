# Provider Pricing and Usage

Pricing is deployment-specific metadata: model/deployment ID, separate input/output USD rates per
million tokens, source, and retrieval date. Missing pricing is unknown, never zero. Rates can become
stale and must be refreshed by the operator; AdaptiveAI does not scrape pricing at startup.

Each gateway record contains request ID, requested and selected model, provider, status, latency,
provider-reported token counts when present, usage provenance, worst-case estimate, and actual-cost
calculation only when provider usage and matching price metadata are both available. Raw prompts and
completions are not stored. “Actual cost” is a calculation, not proof of the provider’s final bill.
