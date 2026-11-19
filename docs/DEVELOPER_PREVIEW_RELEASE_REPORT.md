# AdaptiveAI 0.2.0a1 Developer Preview Release Report

Status: **READY_FOR_OWNER_APPROVAL**. Publication is not authorized.

This prerelease exposes the Phase 6A–7.1 provider-independent gateway, Model Intelligence,
external-evidence, routing-data and deterministic Auto V0 surfaces while preserving the immutable
v0.1.0 release. It is experimental infrastructure, not a proven routing optimizer.

One ProxyAPI basic completion is externally verified. The estimate (0.007648 RUB) reserved an upper
bound based on the configured maximum output; the shorter actual response produced provider-derived
cost 0.001661 RUB, independently matched by the key-budget delta. Exact billing remains provider
controlled.

## Release artifacts

The release handoff records the final wheel/sdist sizes and SHA-256 values externally. Embedding the
sdist's own final hash in a report contained by that sdist would be self-referential and
non-reproducible.

Both clean installs and `pip check` passed on Python 3.12.3. Full tests: 127 passed, 3 expected
skips, 71% coverage. Python 3.11 remains pending CI. Artifact inspection excludes planning, secrets,
weights, caches, evidence databases, virtual environments and Git metadata.

No push, tag, release, PyPI upload or additional paid inference is authorized. Owner permissions
are still required separately for commit, push, GitHub Actions, annotated tag, GitHub prerelease and
artifact attachment.
