# Developer Preview Release Checklist

Proposed version: `v0.2.0a1`; current package remains `0.1.0`.

- [x] Phase 7 implementation preserved before Phase 7.1 changes.
- [x] Exact external candidate and dated official evidence recorded.
- [x] No generic model router or paid fallback in the example.
- [x] Non-network preflight and fail-closed tests added.
- [x] Security, budget, Python, tester and research limitations documented.
- [ ] Separate owner authorization for one external inference request.
- [ ] Live result recorded without secrets or prompt-sensitive data.
- [ ] CI passes on both Python 3.11 and 3.12 at the release commit.
- [ ] Version changed to `0.2.0a1`, changelog finalized and artifacts rebuilt.
- [ ] Artifact contents, licenses, hashes and clean install rechecked.
- [ ] Owner authorizes commit, tag, push and GitHub prerelease.

Do not publish to PyPI, create a tag/release, push, or begin Phase 8 as part of Phase 7.1.
