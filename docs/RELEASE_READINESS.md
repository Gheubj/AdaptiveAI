# Release Readiness

Decision: **READY FOR OWNER APPROVAL**.

Engineering readiness for an experimental release candidate is met: wheel/sdist build, clean-wheel
CLI import, real local non-streaming/streaming inference, mocked API integration, routing/lifecycle
tests, documentation, and CI all exist. This is not production readiness.

All technically actionable pre-approval controls have been completed. Publication remains prohibited
until the owner approves the proposed Apache-2.0 license and attribution, third-party notices, exact
staged manifest, and destination. The workspace has no Git history because this gate intentionally
does not create the initial commit.

## Release-gate evidence (2026-11-18)

- Full suite with the opt-in real local test enabled: **75 passed, 1 skipped in 7.93 s**.
- Whole-package statement coverage: **57%** (3,455 statements, 1,492 missed). This is the measured
  research-plus-product package total; it supersedes earlier partial 75% reporting.
- Ruff formatting and lint: 62 files checked, no findings.
- Staged-snapshot artifacts are approximately 90 KB (wheel) and 157 KB (sdist); exact byte sizes
  are reported from the final immutable staged snapshot in the release-gate handoff.
- Archive inspection: 204 combined entries and zero entries from raw/interim/processed/catalog data,
  models, vendor, reports, virtual environments, or caches.
- Fresh Python 3.12 virtual environment: runtime dependencies installed, `pip check` clean,
  `adaptiveai.__version__ == "0.1.0"`, CLI help and example TOML validation successful.
- `adaptiveai doctor` in the clean release snapshot correctly returns nonzero with actionable
  messages for the intentionally external llama.cpp binary and GGUF weights; registry and RAM checks
  succeed.
- Markdown check: 84 files scanned, zero broken local links.

The build was produced from `git checkout-index`, so unstaged local files could not enter the
artifacts. No release artifact was copied back into the repository or staged.
