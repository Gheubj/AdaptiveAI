# Contributing

Use Python 3.11/3.12 and install `.[research,test,dev]`. Run Ruff, all tests, and `python -m build`.
New claims require frozen protocols, matched panels, paired uncertainty, and negative results. Do
not commit weights, restricted data, caches, secrets, or personal paths. Product changes need tests
for validation, local-only behavior, cleanup, timeouts, and errors. Contributors must have rights to
submit code under the owner-approved license.

Provider changes should extend the bounded provider protocol, keep credentials environment-only,
add exact endpoint/model allowlists, typed/redacted errors, price provenance and offline transport
tests. Never make a live provider test part of the default suite.

Benchmark evidence must include identity/revision, evaluation configuration, provenance,
permissions, missingness and a valid comparability group; synthetic rows must be labeled. To
reproduce Auto V0 decisions, use a fixed TOML candidate/evidence set and `route explain`, then
compare the complete JSON decision. Do not tune against final test data or transfer evidence across
unknown revisions.
