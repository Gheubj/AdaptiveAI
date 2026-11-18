# Routing Dataset Source Audit

Audit date: 2026-11-19. This is a conservative engineering assessment, not legal advice.

## xRouteBench — primary technical candidate

- Owner: `ulab-ai`; implementation by the LLMRouter project.
- Source: [HF dataset card](https://huggingface.co/datasets/ulab-ai/xRouteBench), paper
  `arXiv:2608.06867`.
- Published shape: 245,903 rows, 18 candidate deployments, train/test routing outcomes across
  generic NLP, memory, time-series, video, multimodal math/geometry, and personalized scenarios.
- Fields: prompt, reference, response, metric, score, input/output tokens, latency, model ID, and
  provider-derived historical prices.
- Scientific fit: excellent dense matched supervision; native splits and multiple domains; useful
  for task/prompt/cost/latency routing. Revisions and exact provider deployment configuration remain
  incomplete; personalized scores use an LLM judge; several scenarios transform multimodal inputs.
- Rights: the reviewed dataset card contains citation and usage instructions but no dataset license.
  Model-output and underlying task redistribution rights are not separately enumerated.
- Decision: metadata audit only. No row-level download or local ingestion until the authors clarify
  local research, derived-analysis, model-output, and redistribution permissions.

## RoutingCompendium — secondary candidate

- Owner: Wikit; source cards: [performance](https://huggingface.co/datasets/Wikit/RoutingCompendium-perf)
  and [cost](https://huggingface.co/datasets/Wikit/RoutingCompendium-cost).
- Published shape: 133,253 query rows, 183 cost rows, five source benchmarks, 10–112 candidates per
  split, 460 MB performance data, and precomputed embeddings.
- Scientific fit: broad routing comparison and unseen-pool research, but each split has different
  metrics, candidate identity quality, source protocol, and derived pricing. It has no single native
  train/validation/test convention.
- Rights: the card states that every split inherits its source benchmark license but supplies no
  consolidated component permission matrix. Embedding redistribution and prompt/output rights must
  also be checked per source.
- Decision: no download or ingestion until every selected split has an explicit permission ledger.

## Existing AdaptiveAI LLMRouterBench research

The existing non-redistributed local archive contains 548,046 normalized evaluations, 26,367
queries, 40 source IDs, and 27 datasets. It already supported Phases 2–3.6 and is scientifically
useful for historical fixed-pool research, but exact external model revisions remain unresolved,
constituent redistribution is unclear, and its test/ARC outcomes have been repeatedly inspected.
It is not independent confirmation and is not republished or re-ingested in Phase 6B.5.

## Permission clarification draft (not sent)

> May AdaptiveAI download and analyze xRouteBench locally for non-commercial/open research, store
> derived aggregate statistics, and publish code/aggregate findings without redistributing prompts,
> references, or model responses? Which license applies to dataset rows, model outputs, and each
> underlying benchmark, and are commercial derived analyses permitted?

Sending this request requires owner approval.
