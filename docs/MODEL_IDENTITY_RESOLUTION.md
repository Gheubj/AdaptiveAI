# External Model Identity Resolution

Resolution states are exact, verified alias, possible alias, ambiguous, and unresolved. The current
resolver automatically accepts only an exact canonical ID or one registered alias mapping to one
identity. Multiple alias targets are ambiguous. Display-name or case-insensitive similarity is not
used.

HF identifiers are retained verbatim as `source_model_id`. For lossless storage the adapter creates
a provisional namespace/name identity with unknown revision and quantization, but this is not a
claim that it matches an existing AdaptiveAI model or isolated base weights. The evaluated subject
is a routed/agentic system.

All 20 pilot rows remain unresolved because no reviewed exact revisions or aliases were available.
This is preferable to silently merging an agent submission with its apparent base model.
