# Open-Source Audit

## Repository hygiene

The current workspace contains, but `.gitignore` excludes, a 1.283 GB LLMRouterBench archive,
1.453 GB GGUF weights, 1.15 GB normalized evaluations, a 38 MB MiniLM cache, llama.cpp build/source,
and generated reports. Explicit Hatch exclusions remove raw/models/processed/catalog/vendor/reports
from the sdist. Release archives contain Python code, approved metadata, and documentation only;
staged-snapshot measurements are recorded in `RELEASE_READINESS.md`.

A staged-content credential/private-key/path scan found no secrets or machine-specific paths. The
only email-shaped string is synthetic `ana@example.org` benchmark text. Default logging does not
retain prompts/responses. There is no project commit history, so historical scanning becomes
applicable only after the owner authorizes the initial commit. Do not use `git add -f` on ignored
assets.

## Licenses

Recommended project-code license is Apache-2.0: permissive redistribution/modification with notice,
license, and patent terms, but no warranty. Owner approval of license/attribution is required before
publication. Core dependencies use permissive licenses (HTTPX BSD-3-Clause, psutil BSD-3-Clause;
Pydantic is MIT). llama.cpp is MIT. The two local instruction models and frozen MiniLM encoder are
recorded as Apache-2.0, but model files remain external and require source-specific verification.

LLMRouterBench and constituent data have research/non-commercial and unresolved redistribution
constraints. Raw archives and normalized row-level derivatives must not be published without legal
review. Aggregate research documentation is retained, but this audit is not legal advice.

## Publication controls

The exact staged file list, sizes, purposes, and suitability are recorded in
`STAGED_FILE_MANIFEST.json`; restricted derived data is absent. Before a public push, the owner must
approve that manifest, licensing/ownership, notices, and destination, then authorize the initial
commit and a scan of the resulting history. No commit, history rewrite, or publication was
performed.
