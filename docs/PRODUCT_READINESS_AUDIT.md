# Product Readiness Audit

## Status

AdaptiveAI is technically suitable for an explicitly experimental open-source MVP, with research
limitations. It is not production ready.

Working components include pinned local model discovery, hash metadata, CPU llama.cpp inference,
streaming metric collection, timeout/crash errors, constrained selection, local-only defaults,
CLI inference, loopback HTTP API, provenance, resumable experiments, and 78% project statement
coverage. The Phase 4.5 run exposed and fixed an uncaught localhost `ReadTimeout`; failure and
restart behavior is now tested.

## Release blockers to address in Phase 5

- Package or verify the llama.cpp binary instead of assuming a repository build path.
- Add configuration for dynamic ports, runtime paths, thread/context limits, and model directories.
- Validate API payload types and bounds with a schema; cap prompt and `max_tokens` sizes.
- Expose true streaming at the public API layer; the current backend streams only for metrics.
- Add structured privacy-preserving logs, request cancellation, health details, and backpressure.
- Keep loopback-only binding by default; authentication and a security review are mandatory before
  any non-loopback deployment.
- Automate registry hash verification and give actionable missing-model/backend messages.
- Add persistent multi-model residency or switch hysteresis and sustained concurrency/thermal tests.
- Publish benchmark cards, license notices, reproducible commands, and an explicit experimental
  disclaimer. Do not bundle large model weights.

Technical readiness: experimental. Scientific validation: sufficient for narrow negative and
fixed-model conclusions, insufficient for general hardware-routing superiority. Production
readiness: no.
