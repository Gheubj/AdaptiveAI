# Developer Preview Feature Matrix

| Area | Preview status | Evidence / boundary |
|---|---|---|
| llama.cpp and GGUF local inference | Experimental | Optional external binary/weights; no auto-download |
| Local lifecycle and hardware policies | Locally tested | Host-specific profiles; one resident model |
| OpenAI-compatible BYOK completion | Basic path externally verified | One ProxyAPI non-streaming completion |
| Cloud streaming | Locally tested with fixture | Not externally verified |
| Local/cloud/hybrid scopes | Locally tested | Hybrid cloud selection remains explicit |
| Allowlist, budgets, explicit fallback | Locally tested | Estimates are not billing guarantees |
| Model/deployment identities and capabilities | Implemented public interfaces | Evidence coverage is incomplete |
| Hugging Face benchmark adapter | Fixture/live-metadata bounded adapter | Leaderboard evidence is not isolated quality |
| Evidence store/comparison/permissions | Implemented | Permission ledger does not grant upstream rights |
| Routing supervision/matched outcomes/oracle | Research interfaces | External matched datasets have unresolved permissions |
| Auto V0 / Economy / Manual | Locally tested | Deterministic baseline; may return `INSUFFICIENT_EVIDENCE` |
| Learned prompt-aware router | Not shipped as validated product | Research did not consistently beat baselines |
| CLI, Python client, HTTP explanations | Locally tested | OpenAI compatibility is a documented subset |
