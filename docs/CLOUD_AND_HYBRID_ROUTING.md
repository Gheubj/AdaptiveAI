# Cloud and Hybrid Routing

Scopes are `local`, `cloud`, and `hybrid`. The default is local and `local_only = true`. If either
the request or product configuration enforces local-only, the cloud gateway is not called. Cloud
requires an explicit provider and model from their allowlists. Hybrid only expands eligibility; it
does not authorize a silent fallback or make an unmeasured fastest/quality claim.

An optional `fallback_models` sequence is explicit. Phase 6G considers only the first fallback and
only after `unsupported_model`, a rejection expected before generation. Authentication, credits,
rate-limit, timeout, transport, malformed-response, and interrupted-stream failures are not
retried because a duplicate billable request may have occurred. There are no fallback loops.

Manual model selection still obeys provider, scope, pricing, request, and total-budget constraints.
The local llama.cpp policies and behavior remain independent.
