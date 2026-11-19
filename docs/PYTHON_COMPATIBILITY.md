# Python Compatibility

Supported package range: Python `>=3.11`.

| Runtime | Evidence | Status |
|---|---|---|
| 3.11 | GitHub Actions matrix (`.github/workflows/ci.yml`) | configured; not locally available |
| 3.12 | local full suite, build, install and CLI checks | verified |

The CI matrix builds and tests both 3.11 and 3.12. A local 3.11 interpreter was not present on the
Phase 7.1 host, so no local 3.11 result is claimed. Python 3.13+ is not currently declared or tested.
On 3.12, 125 tests passed and 3 optional tests skipped; a clean wheel install and OpenAI Python
client 3.55.1 localhost compatibility check also passed.
