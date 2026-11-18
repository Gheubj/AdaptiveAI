# Deterministic Eligibility Rules

Eligibility is a hard pre-routing gate with three outcomes: `eligible`, `ineligible`, and `unknown`.
It evaluates deployment availability, local-only policy, provider/model allowlists, required input
modalities, tool support, minimum context, and available memory.

Known violations yield `ineligible`. Missing facts needed to prove compliance yield `unknown`.
Every result includes stable reason codes and readable details. A known violation takes precedence
when other fields are unknown. Manual model selection does not bypass these rules.

This engine does not rank eligible candidates. Ranking remains a separate policy concern, preventing
missing metadata from becoming an accidental score or constraint violation.
