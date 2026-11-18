# Configuration

Configuration is TOML under `[adaptiveai]`; default path is `adaptiveai.toml`, overridden by
`--config` or `ADAPTIVEAI_CONFIG`. Unknown or unsafe fields fail validation.

Supported fields are registry/backend paths, default mode, local-only, loopback host/port, timeout,
request-size/concurrency bounds, keep-alive, switch hysteresis, balanced latency weight, optional
latency/RAM limits, log level, and opt-in research logging. Remote binds are deliberately rejected.
See `adaptiveai.example.toml`. Never store credentials here; cloud providers are disabled in 0.1.0.
