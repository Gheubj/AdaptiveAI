# Capability Profile Specification

Capability profiles are immutable, versioned views tied to one exact `ModelIdentity`. They may
describe input/output modalities, tools, structured output, context window, deployments, and
benchmark evidence references.

Capabilities use three states: `supported`, `unsupported`, and `unknown`. Unknown context length is
also declared in `missing_information`. Evidence references must exist and belong to the same model.
Benchmark evidence is checked pairwise for comparability; mismatches are returned to the caller and
must not be silently averaged.

Profiles contain neither a universal model rank nor an invented quality estimate. Freshness is
represented by the profile creation time and the retrieval timestamps of its evidence. New facts
produce a new profile version instead of rewriting historical evidence.
