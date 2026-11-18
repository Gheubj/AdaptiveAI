# Scoring Validation

The V2 scorer was frozen before model execution. Numerical tasks accept a full answer or a short,
explicit final-answer clause, compare decimal values, and use tolerance
`max(1e-6, 1e-6*abs(reference))`. Multiple untagged candidate numbers are ambiguous and rejected.
JSON extraction requires exactly one parseable object, the exact key set, and field-level equality.
Text scoring applies Unicode/case/terminal-punctuation normalization to the final answer fragment.
Empty and ambiguous responses receive an explicit status and correctness zero.

A manually specified 14-case development suite covered decimal equivalence, answer clauses,
distractor numbers, multiple candidates, factual punctuation, exact JSON fields, missing/extra
fields, multiple objects, and empty output. Observed decisions matched all 14 expected decisions:
zero known false positives and zero known false negatives on this suite. This does not prove scorer
perfection on arbitrary prose. The original Phase 4 exact-match scorer and results were not changed.
