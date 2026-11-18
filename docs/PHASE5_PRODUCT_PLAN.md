# Phase 5 Product Plan

Recommendation: **CONTINUE HARDWARE RESEARCH**, not Product MVP yet.

Before an MVP: replace the 24-query micro-panel with several hundred licensed objective tasks;
support persistent multi-model lifecycle and dynamic free ports; add resumable experiment state;
validate GGUF provenance/revisions automatically; expose the API through a packaged command;
implement structured privacy-preserving logs; add authentication before any non-loopback option;
measure larger but still local models; validate scoring and calibration; test sustained concurrency,
thermal effects, timeouts, and model switching; and perform an independent security review.

The current system is a working research prototype. Its key product insight is that model loading
and RAM are first-class routing constraints, while complex quality routing is unjustified when a
small fast model matches the larger model on the measured endpoint.
