# Phase 6G Test Results

The Phase 6G suite uses `DeterministicOpenAITransport`; it cannot open a network socket. Coverage
includes endpoint validation, hosted/local boundaries, model allowlists, capability rejection,
secret redaction, discovery, ordinary completion, SSE/usage, typed authentication/rate/malformed
errors, strict and permissive pricing, budget rejection, usage accounting, local-only precedence,
CLI inspection without a request, and the full client-to-provider response path.

Final verification on Python 3.12.3:

- 109 collected: 106 passed, 3 expected skips;
- whole-package statement coverage: 70%;
- `cloud.py`: 89%, `cloud_gateway.py`: 81%, combined: approximately 87%;
- Ruff format/check: clean;
- wheel and sdist: built successfully without build isolation or dependency downloads;
- wheel installed into a fresh venv and imported from that venv using the already-installed local
  dependency set (network package installation was intentionally not performed);
- coverage suite elapsed: 20.49 seconds; peak RSS: 576,996 KiB;
- paid API requests, external cloud calls, model downloads, and external dataset calls: zero.

Expected skips are the pre-existing opt-in real-data/local/Hugging Face checks. The standard suite
opened only loopback sockets for local HTTP integration; the provider transport was in-process.
