# Research Results

Phases use different pools and panels and must not be pooled. Phase 2 proprietary-8 TF-IDF achieved
.6155 ID versus Best Single .5994, but ARC-AGI OOD reversed to .2525 versus .4275. Phase 3 neural
methods did not dominate both controls. Phase 3.5 semantic MLP reached .6042 ID/.4210 ARC; revised
gating removed collapse but did not beat constrained TF-IDF.

Phase 4 measured Qwen2.5-0.5B at .532 GB and about 66 tok/s on its long workload, versus SmolLM2
2.288 GB and about 26 tok/s. Phase 4.5 V2 held-out accuracy was .172 versus .416. Complementarity
was 41 both, 2 only Qwen, 63 only SmolLM2, 144 neither. Oracle .424 is post-hoc, not deployable. No
hardware-aware policy beat Fixed Strongest; 16 switches added 24.79 seconds in 24 requests.
