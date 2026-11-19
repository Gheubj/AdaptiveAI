# Installation

Supported Python versions are 3.11 and 3.12. Install the public preview from its immutable tag:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install "git+https://github.com/Gheubj/AdaptiveAI.git@v0.2.0a1"
adaptiveai --version
```

Or download the wheel from the
[v0.2.0a1 GitHub release](https://github.com/Gheubj/AdaptiveAI/releases/tag/v0.2.0a1) and run
`python -m pip install ./adaptiveai-0.2.0a1-py3-none-any.whl`. Published SHA-256 values are:

- wheel: `44bc70fc42160e3c238f62971469164eb61eaabac8b20a8020a395523289528d`;
- sdist: `deb50a40f56ee821f788be8bb352b8cb1ef210b50b6c87617a79eedcdd90e236`.

Contributors clone the repository and use `pip install -e '.[research,test,dev]'`.

A wheel contains the Python package only, not examples, llama.cpp, GGUF weights, benchmark archives,
reports or caches. Clone the exact tag when following examples that use repository TOML files.

Provide a CPU-compatible `llama-server` binary and configure `backend_path`. Create a registry using
the schema in `data/local_model_registry.json`: model ID, GGUF path, family, parameters,
quantization, license, context length, and optional SHA-256. Weights are never downloaded
automatically. Run `adaptiveai doctor`, then `adaptiveai models list --verify-hashes`.
