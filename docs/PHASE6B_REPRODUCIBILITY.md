# Phase 6B Reproducibility

The live pilot snapshot ID is `hf-swe-verified-6642b94417f6bc7f`, SHA-256
`6642b94417f6bc7f6462e2af727a6111470e3c80bf79e70b4795ac44ffa9b61a`, size 59,880 bytes,
schema/parser version 1.0, and retrieval time `2026-11-18T18:50:56.563619Z`. It is private local
cache because redistribution permission is unknown.

Deterministic tests use small synthetic payloads, never live values. Offline replay accepts an
explicit snapshot. Manifests record source/accepted/rejected counts and incomplete status. A
content hash change indicates a source update; importing it appends new/conflicting evidence rather
than overwriting prior rows. Dry-run reports the prospective store update without mutation.

There is no scheduler. A future refresh should be explicit, bounded, compare snapshot hashes, audit
schema/terms changes first, preserve retrieval history, and require review before profile promotion.
The optional live test is controlled by `ADAPTIVEAI_LIVE_HF=1` and is not required by CI.
