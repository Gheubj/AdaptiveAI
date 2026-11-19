# Developer Preview Test Results

Release-candidate verification on Python 3.12.3 collected 130 tests: **127 passed and 3 expected
opt-in skips**. Statement coverage was **71%**. The suite includes CLI/SDK, localhost HTTP E2E,
streaming, budget, local-only, fallback and route-explanation coverage. Ruff format/check and
`git diff --check` passed.

Wheel and sdist built successfully. Each installed with dependencies into a separate fresh Python
3.12 virtual environment; `pip check` and `adaptiveai --version` passed for both. Python 3.11 was not
installed locally and remains pending an owner-authorized GitHub Actions run. No paid inference,
model download or restricted dataset access occurred.

The first sandboxed pytest attempt blocked six localhost socket tests; rerunning the identical suite
with loopback permission passed. This was an execution-policy constraint, not a test relaxation.
