# External Provider Smoke-Test Procedure

Not executed. Current status: `READY_FOR_OWNER_AUTHORIZATION`. Inspect, estimate and run the
non-network preflight first:

```bash
adaptiveai --config adaptiveai.toml providers list
adaptiveai --config adaptiveai.toml providers estimate --provider PROVIDER --model MODEL \
  --input-tokens 16 --max-output-tokens 8
adaptiveai --config examples/openrouter_phase7_1.toml providers smoke-plan \
  --provider openrouter --model inclusionai/ling-3.2-flash:free
```

Verify provider, deployment, model, endpoint, token limit, price source/date, then obtain explicit
owner authorization for one request and maximum cost. Only then run:

```bash
adaptiveai --config adaptiveai.toml chat 'Reply with: ok' --scope cloud \
  --provider PROVIDER --model MODEL --max-tokens 8 --max-estimated-cost MAX_USD \
  --allow-paid-cloud
```

Streaming is a separately authorized potentially billable request. Key presence is not permission.
The exact proposed request is recorded in `EXTERNAL_SMOKE_AUTHORIZATION.md`. Readiness does not
authorize execution; external compatibility remains unverified.
