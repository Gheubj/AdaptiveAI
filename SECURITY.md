# Security Policy

AdaptiveAI is an experimental Developer Preview, not a hardened public multi-user service.

Report suspected vulnerabilities privately through GitHub Security Advisories for
`Gheubj/AdaptiveAI`. Do not include API keys, prompts, model data or exploit traffic against systems
you do not own. Maintainers will acknowledge reports when available; no response SLA is promised.

Only the latest published release receives best-effort security fixes. Keep credentials in
environment variables, use provider/model and endpoint allowlists, retain local-only defaults, set
explicit budgets, and never expose the loopback server publicly without an independent security
boundary. See `docs/PRIVACY_AND_SECURITY.md` and `docs/BYOK_SECURITY.md` for current limitations.
