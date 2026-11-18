# Phase 6A Report — Model Intelligence Foundation

## A. Outcome

Phase 6A adds a provider-independent, evidence-first model intelligence foundation. It is an offline
software architecture result, not a new model-quality experiment. Phase 6B was not started.

## B. Implemented architecture

- exact family/model/revision/quantization, provider, alias, deployment, and evaluation identities;
- typed evidence with explicit missingness, reliability, provenance, and permissions;
- structured comparability diagnostics without a universal rank;
- deny-by-default redistribution decisions;
- versioned tri-state capability profiles;
- deterministic eligible/ineligible/unknown decisions with structured reasons;
- fixture-only benchmark adapter contract;
- a compatibility adapter that leaves the v0.1.0 router authoritative.

## C. Scientific and product safeguards

No absent capability, confidence, or quality value is fabricated. Unknown revisions and missing
constraints remain visible. Incompatible evidence is not pooled. The implementation separates
base models, provider deployments, and routed systems and does not use final tests or ARC-AGI for
selection.

## D. Data, compute, and cost

Only synthetic fixture data was used. There were no paid APIs, model downloads, network benchmark
runs, training jobs, cloud resources, or distributed computation. The work is CPU-only and well
within the 16 GB memory constraint.

## E. Compatibility

The Phase 5 routing engine and all public interfaces are unchanged. Frozen adapter tests compare
legacy and compatibility results. Historical reports and v0.1.0 release artifacts are unchanged.

## F. Validation

Focused tests cover identity, time-bounded aliases, explicit unknowns, evidence hashing and
deduplication, comparability mismatches, permission denial, profile ownership, all eligibility
states, fixture normalization, and legacy delegation. Final verification: **82 passed, 2 optional
integration tests skipped**, Ruff clean, formatting clean for tracked source/test/example paths,
and 60% whole-package statement coverage. Phase 6A modules have 85–100% focused coverage.

Wheel and sdist builds passed. Archive inspection found and then fixed an sdist rule that initially
included the untracked `planning/` directory; rebuilt archives exclude planning, raw/processed/model
data, vendor code, reports, virtual environments, and caches. The rebuilt wheel imports correctly
from a clean target with the project environment's declared dependencies. These are local
verification artifacts and were not published.

## G. Limitations

No real source has yet been admitted through the permission gate. Capability facts are therefore
fixtures, not a production catalog. Alias history, provider availability, prices, latency, and
capabilities can change and need source-specific freshness policy. Eligibility is a gate, not a
router or a guarantee that inference will succeed.

## H. Decision

Phase 6A can be accepted when final tests, lint, build, archive inspection, and isolated install pass.
Phase 6B remains a separately reviewed proposal. No release, push, tag, or v0.1.1 publication is
authorized by this phase.
