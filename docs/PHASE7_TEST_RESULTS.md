# Phase 7 Test Results

Python 3.12.3 final verification:

- 127 collected, 124 passed, 3 expected opt-in skips, 0 failed;
- whole-package statement coverage 71%;
- focused coverage: Auto V0 95%, cloud adapter 92%, gateway 85%, local test provider 78%;
- Ruff formatting and lint clean;
- coverage run 21.57 seconds, peak RSS 576,356 KiB;
- 10,000 synthetic Auto decisions averaged 29.7 microseconds router-only;
- 20 direct localhost provider requests averaged 1.56 ms;
- Python 3.11 was not installed locally and was not claimed tested;
- external calls, paid requests, model downloads and training: zero.
- documented two-process quick start passed: manual response, Auto selection, dry-run explanation,
  four SSE events and local-only rejection were observed through localhost ports 8088/8099.

Packaging succeeded without dependency downloads. The wheel was installed into a fresh venv and
imported from that venv using the existing offline dependency set. Wheel SHA-256:
`545ed7026a2431e825d5d1a02e6a0c8d86118994c50a9af21959638eb6a56fb1`. The sdist hash is recorded
after the final documentation rebuild.

The three skips require an explicit live Hugging Face flag, real llama.cpp setup, or a private real
archive. Local latency is test-provider behavior and says nothing about commercial providers.
