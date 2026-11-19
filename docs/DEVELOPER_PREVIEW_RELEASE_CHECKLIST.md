# Developer Preview Release Checklist

Release-candidate version: `0.2.0a1`; proposed tag: `v0.2.0a1`.

- [x] Phase 7 implementation preserved before Phase 7.1 changes.
- [x] Exact external candidate and dated official evidence recorded.
- [x] No generic model router or paid fallback in the example.
- [x] Non-network preflight and fail-closed tests added.
- [x] Security, budget, Python, tester and research limitations documented.
- [x] Separate owner authorization consumed for exactly one external inference request.
- [x] Live result recorded without credentials or private prompt data.
- [ ] CI passes on both Python 3.11 and 3.12 at the release commit.
- [x] Version changed to `0.2.0a1`, changelog finalized and artifacts rebuilt.
- [x] Artifact contents, licenses, hashes and clean wheel/sdist installs rechecked.
- [ ] Owner authorizes commit, tag, push and GitHub prerelease.

Python 3.12 passes locally. Python 3.11 and GitHub Actions remain pending owner authorization. Do not
publish to PyPI, create a tag/release, push, or begin a new research phase during preparation.
