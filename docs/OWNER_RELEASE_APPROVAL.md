# Owner Release Approval — AdaptiveAI 0.1.0

This document records the remaining owner decisions for the proposed first public release. It does
not grant approval. No commit, tag, push, GitHub release, or PyPI publication has been performed.

## Licensing and provenance

- Proposed project license: Apache License 2.0. `LICENSE` is the canonical, byte-identical text.
- The owner must confirm that Apache-2.0 is the intended license and supply or approve the copyright
  holder/name and year convention. No project `NOTICE` file is presently required by a detected
  bundled attribution, but the owner must confirm that conclusion.
- The staged source has no copied copyright/SPDX headers and no vendored implementation. The owner
  must confirm ownership or publication authority for the project code and documentation.
- `THIRD_PARTY_NOTICES.md` inventories runtime dependencies, external model/backend components, and
  restricted research data. Dependencies are not vendored. This is a technical inventory, not legal
  advice.

## Public files

The exact proposed first commit is the current Git index. Its machine-readable inventory is
`docs/STAGED_FILE_MANIFEST.json`; every entry records path, byte size, file type, purpose, and
publication suitability. Approval must cover that exact manifest, not an unstaged working tree.

Excluded and locally preserved material includes raw/interim/processed/catalog datasets, GGUF model
weights, encoder caches, llama.cpp source/build outputs, generated reports, virtual environments,
Python/test caches, private configuration, and build artifacts. These exclusions include roughly
1.28 GB of raw benchmark data, 1.45 GB of model weights, 1.15 GB of normalized evaluations, a 38 MB
encoder cache, a 307 MB backend source/build tree, and generated report artifacts.

## Security and privacy review

- Staged-content scans found no credential-like secrets, private keys, machine-specific absolute
  paths, binaries, symlinks, oversized blobs, or personal email addresses.
- `ana@example.org` is the sole email-shaped string and is synthetic benchmark text.
- Row-level restricted benchmark data, model weights, caches, and generated reports are not staged.
- The repository has no prior commits, so historical secret scanning is not applicable until the
  owner authorizes creation of the first commit.

## Packaging and tests

Release-gate evidence must be read together with `docs/RELEASE_READINESS.md` and the generated staged
manifest. The candidate was built from an extracted Git-index snapshot, not from unstaged files.
The wheel is approximately 90 KB and the sdist approximately 157 KB; exact final-snapshot sizes are
reported in the release-gate handoff. Archive inspection found no restricted paths. A fresh Python
3.12 installation passed dependency, import, CLI, and configuration checks.
`doctor` produced the expected actionable failure for external backend/weights. The full suite passed
75 tests with one intentional skip; whole-package statement coverage is 57%.

## Draft release notes

AdaptiveAI 0.1.0 is an experimental research-oriented local LLM routing framework. The initial
candidate provides hardware discovery, external local-model registration, lifecycle management,
multiple routing modes, a Python client, CLI, local HTTP/SSE API, reproducible research components,
and extensive limitations/methodology documentation. It does not claim production readiness or
routing superiority over a fixed strongest-model baseline. Model weights, llama.cpp, and restricted
datasets are not distributed.

## Proposed publication

Proposed sequence after explicit approval: create the exact reviewed initial commit in the owner's
chosen public GitHub repository; verify the resulting history; optionally create a signed/annotated
`v0.1.0` tag and GitHub release; publish the reviewed artifacts to PyPI only if separately approved.
Public visibility, repository destination, tagging, and package publication remain undecided.

Suggested repository description:

> Experimental, local-first LLM routing framework with hardware-aware policies and reproducible
> routing research.

Suggested topics: `llm-routing`, `local-llm`, `machine-learning`, `pytorch`, `llama-cpp`,
`hardware-aware`, `research`, `python`.

## Required owner decisions

The owner must explicitly approve or amend all of the following:

1. Apache-2.0 as the project license.
2. Copyright holder/name, year convention, code/documentation ownership, and whether a `NOTICE` file
   is required.
3. The technical third-party notice inventory and any additional legal review.
4. Public visibility and the exact repository owner/name/destination.
5. The exact staged manifest and creation of the initial commit.
6. Whether `v0.1.0`, a GitHub release, and PyPI publication are authorized now, later, or not at all.

Until those decisions are recorded, the candidate is **READY FOR OWNER APPROVAL**, not approved for
publication.
