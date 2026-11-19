# Phase 6A Compatibility

Phase 6A is additive. The v0.1.0 public request/response dataclasses, routing modes, diagnostics,
local lifecycle, CLI, HTTP API, SSE frames, and client remain unchanged. The new
`CompatibilityRoutingAdapter` delegates `select` and `eligible` directly to the existing
`RoutingEngine`.

A frozen test compares legacy and adapter diagnostics for the same request and verifies the same
unknown-model error. Existing Phase 5 product tests remain unchanged. The model-intelligence layer
does not reinterpret the historical `estimated_quality` field: it only prevents new evidence and
capability code from manufacturing such values.

Phase 6A does not alter historical experimental artifacts, v0.1.0, its Git tag, or its GitHub
release.
