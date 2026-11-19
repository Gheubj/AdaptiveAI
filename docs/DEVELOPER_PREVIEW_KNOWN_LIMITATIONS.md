# Developer Preview Known Limitations

- Auto V0 is deterministic and evidence-aware, not a calibrated learned quality predictor. It does
  not always choose the best model and may return `INSUFFICIENT_EVIDENCE`.
- Neural routing has not consistently beaten simple baselines. Complementarity is essential, and
  switching overhead can negate latency benefits.
- The Phase 4.5 local pool had only 0.008 oracle quality headroom above its strongest fixed model.
- SWE-bench leaderboard imports do not directly establish isolated base-model quality or universal
  rankings.
- One ProxyAPI basic completion validates only that narrow path. External streaming, tools,
  concurrency, reliability, revision coverage and routing superiority are unverified.
- Strict SSRF mode fails closed because the hosted transport does not connection-pin resolved IPs.
  The gateway is not hardened for untrusted public multi-user deployment.
- Estimates reserve worst-case configured token usage; provider tokenization, usage reporting and
  billing remain external. No implicit currency conversion occurs.
- External matched routing datasets retain unresolved permission questions. No restricted dataset,
  cache, evidence database, model weight or private prompt is distributed.
