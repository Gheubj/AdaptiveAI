# Third-Party Notices

AdaptiveAI project code is proposed for release under Apache License 2.0, subject to owner
confirmation. That proposal does not relicense the components below.

## Runtime dependencies

AdaptiveAI declares but does not vendor these packages. Their own distributions contain the
controlling license text.

| Component | Use | Recorded license |
|---|---|---|
| HTTPX | HTTP client and streaming | BSD-3-Clause |
| Pydantic | Request/configuration validation | MIT |
| psutil | Hardware/process inspection | BSD-3-Clause |

Optional research dependencies include NumPy, pandas, SciPy, scikit-learn, Matplotlib, PyArrow,
PyTorch, and sentence-transformers. They are not bundled in AdaptiveAI release artifacts and remain
under their respective upstream licenses. Exact dependency versions and notices must be reviewed
when producing a locked downstream environment.

## External inference backend

llama.cpp is an external MIT-licensed project. Its source/build tree and binary are excluded from
the public AdaptiveAI commit and release artifacts. Users provide their own compatible backend.

## Model weights and encoders

Qwen2.5-0.5B-Instruct, SmolLM2-1.7B-Instruct, their community GGUF quantizations, and
all-MiniLM-L6-v2 are separately obtained artifacts. The research registry records Apache-2.0 for
the referenced model families/encoder, but AdaptiveAI does not bundle or relicense any weights.
Users and the release owner must verify the exact upstream repository, revision, quantizer terms,
and license before redistribution.

## Datasets and research artifacts

LLMRouterBench and some constituent benchmark data carry research/non-commercial or otherwise
unresolved redistribution restrictions. Raw archives, normalized row-level datasets, response
caches, embeddings, checkpoints, and generated reports are excluded from the public commit. Public
documentation contains aggregate findings only. This inventory is technical due diligence, not
legal advice.
