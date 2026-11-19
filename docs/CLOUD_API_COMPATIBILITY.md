# Cloud API Compatibility

The first adapter implements a narrow OpenAI-compatible subset:

- `GET /v1/models` for explicit discovery;
- `POST /v1/chat/completions` with model, messages, temperature, max tokens, and stream;
- ordinary JSON responses, SSE `data:` chunks, `[DONE]`, and optional usage;
- bearer BYOK authentication and typed status/transport errors.

It does not promise compatibility with Responses API, tools, images, audio, logprobs, JSON schemas,
provider-specific reasoning controls, or every SSE variant. Unknown mandatory capabilities are
rejected at configuration time. Discovery is non-generative but still an explicit network request;
startup, install, doctor, provider inspection, and standard tests do not invoke it.
