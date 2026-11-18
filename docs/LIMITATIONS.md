# Limitations

Quality estimates are task/model/version specific; latency and RAM profiles are host/runtime
specific. V2 is templated and covers two small models, with only .008 oracle headroom above
SmolLM2. No general routing superiority, production reliability, energy efficiency, security, or
cloud comparison is established.

The server supports one resident model, bounded low concurrency, and a chat subset. It lacks auth,
TLS, distributed queues, multi-model residency, thermal management, and GPU validation. Dynamic
free-port selection has a small bind race. Stream cancellation closes HTTP but lacks a backend-native
acknowledgement. Third-party licenses require owner review.
