# External Provider Smoke-Test Procedure

Not executed. Inspect and estimate first:

```bash
adaptiveai --config adaptiveai.toml providers list
adaptiveai --config adaptiveai.toml providers estimate --provider PROVIDER --model MODEL \
  --input-tokens 16 --max-output-tokens 8
```

Verify provider, deployment, model, endpoint, token limit, price source/date, then obtain explicit
owner authorization for one request and maximum cost. Only then run:

```bash
adaptiveai --config adaptiveai.toml chat 'Reply with: ok' --scope cloud \
  --provider PROVIDER --model MODEL --max-tokens 8 --max-estimated-cost MAX_USD \
  --allow-paid-cloud
```

Streaming is a separately authorized potentially billable request. Key presence is not permission.
Readiness: `READY_FOR_OPT_IN_LIVE_SMOKE`; external compatibility remains unverified.
