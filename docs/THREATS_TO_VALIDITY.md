# Threats to Validity

- **Construct validity:** heterogeneous upstream scores do not necessarily measure one construct.
- **Judge bias:** LLM-as-judge tasks can favor particular styles or model families.
- **Selection bias:** available model/query panels may omit failures or unavailable models.
- **Temporal validity:** catalog availability and pricing change; historical and current prices differ.
- **Identity ambiguity:** aliases and versioned releases make cross-provider mapping risky.
- **Latency ambiguity:** aggregate benchmark duration is not per-request latency.
- **Leakage:** paraphrases, templated questions, and benchmark contamination can cross splits.
- **Hardware confounding:** runtime, quantization, batching, thermal state, cache state, and software
  versions affect local measurements.
- **Missing-not-at-random:** absent responses may reflect model failures rather than random loss.
- **Reproducibility:** proprietary models can change behind stable IDs.
- **Approximate duplicates:** conservative blocking can miss paraphrases; looser blocking can merge
  distinct templated questions. Oversized candidate blocks are deliberately skipped.
- **Licensing:** archive use is limited to non-commercial academic research/result reproduction;
  constituent dataset rights and raw redistribution remain unresolved.
- **Repeated releases:** overlapping HLE/MMLU-Pro subsets contain 237 conflicting pair scores.
- **Upstream evaluation data:** custom router splits partition mostly benchmark evaluation inputs;
  they do not transform these inputs into original benchmark training data.
- **Zero monetary cost:** local-model cost omits hardware, energy, and loading overhead.
- **OOD choice:** ARC-AGI is one distribution shift and cannot establish general OOD robustness.
- **Pool selection:** Phase 1B coverage analysis inspected the full archive before pools were frozen;
  this can introduce test-coverage selection bias.
- **Shortcut learning:** TF-IDF can identify benchmark style/source rather than model competence;
  its strong ID and poor ARC-AGI results are consistent with this threat.
- **Multiplicity:** several routers, datasets, seeds, and resolution policies were inspected without
  a preregistered multiplicity correction; intervals are estimation, not universal confirmation.
- **Previously inspected holdouts:** Phase 2 exposed test and ARC-AGI before Phase 3; neural holdout
  results are exploratory rather than fresh confirmation.
- **Lexical hashing:** trainable hashed word features can still learn source style and collide; they
  do not establish semantic reasoning.
- **Gate objective:** historical costs and winner targets encourage cheap-model collapse; one failed
  formulation cannot reject every constrained-learning alternative.

## Phase 3.5 additions

- ID test and ARC-AGI were inspected in earlier phases; Phase 3.5 estimates are exploratory.
- MiniLM was chosen before evaluation, but encoder truncation and architecture choices add degrees
  of freedom. No multiplicity correction covers all methods/datasets.
- Train-only leave-dataset-out folds share upstream collection and model pool; they are not external
  validation.
- Historical monetary costs omit local hardware and may be stale. MiniLM CPU timing is machine-
  specific and excludes candidate LLM inference.
- The primal-dual gate optimizes a soft policy but deploys hard argmax decisions.

## Phase 3.6 additions

- No independent benchmark passed exact model-panel eligibility; external validity remains open.
- The matched-budget audit repeats an inspected test and cannot select a deployable winner.
- CPU RSS deltas are process-state dependent and timings are machine/configuration specific.
- Router overhead excludes downstream LLM generation, queuing, switching, and energy.
- Public benchmark licenses can inherit constituent restrictions even when repository code is open.

## Phase 4 additions

- Only two small quantized models and eight held-out prompts were evaluated; strict exact match is
  sensitive to extra prose and uncertainty is large.
- Relaxed containment scoring was added after inspection and is explicitly exploratory.
- Process-cold measurements retain OS page cache; thermal/background state varies.
- RSS omits some shared/system effects, and no readable energy counter was available.
- The API and hybrid provider layer are prototypes; no real cloud comparison occurred.

## Phase 4.5 additions

- V2 is locally authored and templated; strong internal reproducibility does not imply broad
  natural-query generalization or absence of pretraining familiarity with underlying facts.
- Improved scoring and V2 task composition differ from Phase 4, so the changed model ranking cannot
  be attributed to scoring alone.
- Only two models were evaluated. Their complementarity is asymmetric and cannot establish how a
  richer pool would route.
- The 250-query confirmatory inference is single-seed deterministic decoding. Bootstrap estimates
  query sampling uncertainty, not decoding stochasticity.
- Tail-latency constraints used Phase 4 profile predictions and were miscalibrated for V2 response
  lengths. Real execution covers only 24 queries per policy.
- RSS is sampled after inference rather than a high-frequency process peak; energy remains N/A.

## Phase 5 additions

- Product profiles inherit Phase 4/4.5 host and workload bias and can become stale after runtime,
  quantization, prompt, model, or hardware changes.
- Lifecycle hysteresis is a transparent heuristic, not an optimal scheduler.
- Mocks cannot reproduce every disconnect, OS signal, malformed stream, thermal state, or race; real
  smoke coverage is intentionally small.
- The development server is not evidence of production security or availability.
- License inventory is technical due diligence, not legal advice. No initial Git history exists, so
  historical secret auditing was impossible.
