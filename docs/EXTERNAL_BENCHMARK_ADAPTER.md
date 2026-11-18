# Hugging Face SWE-bench Verified Adapter

`HuggingFaceSWEVerifiedAdapter` uses the documented anonymous HF REST endpoint. It has explicit
limits for result count, response bytes, connect/read timeout, retries, total requests, and offline
mode. The Phase 6B pilot used one request, no retries, a 1 MiB byte ceiling, and accepted at most 20
records.

The parser validates each row independently, reports rejected indices, preserves source model ID,
source URL, submission filename/PR-derived record ID, original value/percent scale, snapshot hash,
retrieval time, and verification flag. Empty, malformed, oversized, rate-limited, HTTP-failed, and
network-failed imports return typed errors. A result limit produces an explicitly incomplete import.

No HF token is required or read. The adapter does not download datasets, task text, submissions,
logs, trajectories, or model weights. Default unit tests use `httpx.MockTransport`.

CLI examples:

```bash
adaptiveai intelligence sources
adaptiveai intelligence permissions
adaptiveai intelligence import --live --max-results 20
adaptiveai intelligence evidence --source-model-id org/model
adaptiveai intelligence compare org/model other/model
```

Use `--snapshot PATH` instead of `--live` for offline replay and `--dry-run` to validate without
writing evidence or snapshots.
