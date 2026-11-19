# Auto Routing V0

Auto V0 is a transparent deterministic baseline, not a learned router and not evidence of routing
superiority. Its replaceable `AutoRoutingPolicy` classifies locally, applies hard eligibility,
admits only compatible evidence, and otherwise abstains.

Categories are coding, mathematics, reasoning, writing, extraction, factual QA, data analysis, tool
use, and unknown/general. The method, matched rules, and ambiguity are returned; they are not
calibrated confidence. Zero or multiple category matches yield unknown/general.

Availability, local-only, scope, provider, capability, context, pricing, and budget gates run before
ranking. Quality rows require matching task, known revision, provenance and one shared comparison
group covering at least two candidates. Multiple groups, incompatible rows and unrelated system
evaluations do not form a ranking. Agentic SWE-bench is not base-model coding evidence.

`Economy` picks the lowest known preflight cost. `Manual` validates an explicit selection. Legacy
modes retain their meanings. Under insufficient evidence, policy either uses a user-configured
default or returns `INSUFFICIENT_EVIDENCE`; it never silently selects an unknown paid provider.

Explanations include provider/deployment/model, category, eligible/excluded candidates and reasons,
evidence IDs, missing information, cost status, selection reason and router-only overhead. They
exclude prompt/response text and credentials.

## Usage

```bash
adaptiveai --config examples/phase7_alpha.toml route explain \
  "Debug this Python exception" --mode auto --scope hybrid
adaptiveai --config examples/phase7_alpha.toml route explain \
  "Summarize this paragraph" --mode economy --scope hybrid
```

These commands are dry-run explanations and do not infer. The included evidence is synthetic and
tests behavior only. A selected cloud candidate still requires an available credential, explicit
execution acknowledgement, applicable owner authorization, and all gateway budget controls.
