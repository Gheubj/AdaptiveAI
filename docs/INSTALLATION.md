# Installation

Supported Python versions are 3.11 and 3.12. Create an isolated environment and run
`pip install -e '.[local]'`; contributors use `pip install -e '.[research,test,dev]'`. A wheel
contains the Python package only, not llama.cpp, GGUF weights, benchmark archives, reports, or
caches.

Provide a CPU-compatible `llama-server` binary and configure `backend_path`. Create a registry using
the schema in `data/local_model_registry.json`: model ID, GGUF path, family, parameters,
quantization, license, context length, and optional SHA-256. Weights are never downloaded
automatically. Run `adaptiveai doctor`, then `adaptiveai models list --verify-hashes`.
