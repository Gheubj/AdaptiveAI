# Budget Enforcement

Before a request, AdaptiveAI estimates input tokens conservatively from character count and uses the
configured maximum output tokens. It then calculates a worst-case amount from deployment pricing.
Per-request and cumulative limits are checked before transmission. Strict mode rejects absent price
metadata or non-USD comparison; permissive mode allows the call but reports cost as unknown.

This is a guardrail, not a billing guarantee: tokenization, provider-side additions, dynamic prices,
taxes, caching, reasoning tokens, and delayed usage can differ. Set provider-side hard limits too.
No Phase 6G test performed a paid request; total real spend was USD 0.
