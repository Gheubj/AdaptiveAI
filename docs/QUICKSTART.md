# Quickstart

1. Copy `adaptiveai.example.toml` to `adaptiveai.toml` and edit backend/registry paths.
2. Run `adaptiveai doctor`, `adaptiveai hardware inspect`, and `adaptiveai models list`.
3. Test `adaptiveai chat "Reply with ready" --mode fastest`.
4. Start `adaptiveai serve`; it listens on `127.0.0.1:8088` by default.
5. Run `examples/basic_chat.py`, `examples/routing_modes.py`, or `examples/streaming.py`.

Use `--model <registry-id>` for explicit selection. Quality mode requires a real estimate in the
profile file. No benchmark download is required to serve configured models.
