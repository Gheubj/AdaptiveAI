# Model Complementarity

On the 250-query held-out test, Qwen2.5-0.5B was correct on 43 queries and SmolLM2-1.7B on 104.

| Outcome | Queries |
|---|---:|
| Both correct | 41 |
| Only Qwen correct | 2 |
| Only SmolLM2 correct | 63 |
| Both incorrect | 144 |

Disagreement is 0.260 and binary correctness correlation (phi) is 0.497. Oracle accuracy is 0.424
(query bootstrap 95% CI 0.364–0.488), a gain of 0.252 over Fastest but only 0.008 over the
validation-selected Best Single. Thus the models differ, but complementarity is overwhelmingly
one-directional: SmolLM2 supplies 63 unique successes and Qwen only two. The current pool has almost
no oracle headroom above Fixed Strongest, so a learned router cannot plausibly produce a large
quality gain without adding a genuinely complementary model.

No additional weight was downloaded. A future candidate should be a CPU-compatible, Apache/MIT
instruction GGUF selected on development-only evidence for complementary programming and arithmetic
capability; exact revision, Q4 size, RAM estimate, and license must be documented and separately
approved before download.
