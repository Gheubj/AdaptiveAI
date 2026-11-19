# Phase 7.1 Security and Budget Review

Decision: safe to prepare; not authorized to execute externally.

Controls verified: environment-only BYOK reference, HTTPS and hostname allowlist, exact model
allowlist, exact upstream pin, provider fallback disabled, no automatic paid retry, client rate
limit, response-size bound, timeout, typed/redacted errors, strict known pricing, per-request budget,
and atomic total-budget reservation.

The proposed price snapshot is zero USD, but this does not eliminate account, policy, routing, or
pricing risk. The request must be rejected if official price changes, the model/upstream disappears,
the provider constraint is ignored, pricing is unknown, or the owner has not approved every field.
The CLI's historical `--allow-paid-cloud` acknowledgement is an execution safety catch; it is not
owner authorization and its name does not imply that a zero-price request is paid.

`data_collection = "deny"` is best-effort routing metadata, not proof of Zero Data Retention. Only a
synthetic phrase is proposed. Secrets and content are excluded from diagnostics. SSRF protection
remains fail-closed when strict connection pinning cannot be guaranteed.
