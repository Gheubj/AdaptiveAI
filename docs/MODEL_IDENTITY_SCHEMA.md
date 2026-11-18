# Model Identity Schema

Phase 6A separates facts that provider catalogs often collapse:

- `ModelFamily`: owner namespace and family;
- `ModelIdentity`: model name, exact revision status, and quantization;
- `ProviderIdentity`: the serving organization, independent of the model author;
- `ProviderAlias`: a time-bounded provider name mapped to an exact identity;
- `DeploymentIdentity`: a concrete provider deployment and optional region/endpoint kind;
- `EvaluationConfiguration`: harness, harness version, parameters, environment, and a stable hash.

Canonical IDs are normalized and include explicit `revision-unknown` and
`quantization-unknown` components. An alias such as `latest` is never treated as an immutable model
revision. A declared or verified revision must contain a revision value; unknown revisions cannot
carry one. Evaluation subjects reject deployments whose embedded model differs from the evaluated
model.

The schema is implemented in `adaptiveai.identity` using frozen, strict Pydantic models. It does
not infer identity from fuzzy names.
