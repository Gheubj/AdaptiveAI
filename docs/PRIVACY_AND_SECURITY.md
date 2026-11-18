# Privacy and Security

Defaults are local-only, loopback-only, single concurrency, bounded requests, and no raw prompt or
response logging. Research logging is opt-in. AdaptiveAI does not enable cloud inference.
Subprocess arguments are arrays, not shell commands.

The development server has no authentication or TLS and is not production hardened. Remote binding
is rejected. Any external proxy must add authentication, TLS, rate limiting, authorization,
isolation, and security review. GGUFs and binaries are trusted local inputs; verify provenance and
hashes. Prompt content is retained only in process memory unless external tooling records it.
