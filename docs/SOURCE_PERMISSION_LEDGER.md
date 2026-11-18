# Source Permission Ledger

Each source records independent states for metadata access, local ingestion, local analysis,
derived use, redistribution, and commercial use, plus attribution requirements and notes. States
are `allowed`, `prohibited`, `unknown`, or `not_applicable`.

Export is deny-by-default. `evaluate_export` permits redistribution only when redistribution is
explicitly allowed, the attribution requirement is known, and any required attribution text is
present. Local analytical permission does not imply redistribution permission. Unknown commercial
terms are preserved rather than interpreted.

Phase 6A includes only synthetic fixture-backed adapter data. It adds no third-party dataset,
provider scrape, model output, or redistributable external benchmark artifact. Before Phase 6B,
each candidate source needs an owner-readable license/terms record, retrieval date, intended use,
attribution text, and an explicit redistribution decision.
