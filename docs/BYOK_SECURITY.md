# BYOK Security

Configuration stores an environment-variable name, never a credential. The adapter resolves the
value immediately before a request and does not persist it. Errors, diagnostics, usage records, and
mock fixtures exclude headers, prompts, responses, and keys. AdaptiveAI operates no key custody or
proxy infrastructure.

Hosted-mode endpoints require HTTPS and an exact hostname allowlist. Userinfo, URL queries, and
fragments are rejected. DNS is resolved before client creation and every resolved private,
loopback, link-local, multicast, reserved, or unspecified address is rejected. Redirects are off,
response bytes and timeouts are bounded, and no automatic paid retry is performed. Production
operators must additionally pin trusted provider domains and apply an egress firewall; application
DNS validation alone cannot fully eliminate DNS rebinding/TOCTOU risk.

Plain HTTP is accepted only in explicit developer mode for localhost/loopback. This is intended for
local mock or compatible servers, never hosted multi-tenant deployment. Cancellation closes the
upstream stream where supported; it is not a promise that a provider will stop billing.
