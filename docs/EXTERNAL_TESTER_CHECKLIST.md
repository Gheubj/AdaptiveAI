# External Tester Checklist

Use only non-sensitive synthetic prompts and a disposable BYOK credential with the lowest practical
account cap. Confirm the exact repository commit and follow `DEVELOPER_PREVIEW_QUICKSTART.md`.

- Record OS, architecture, Python version, install command and AdaptiveAI commit.
- Run `adaptiveai doctor` and offline tests first.
- Start with localhost fixtures; confirm chat, stream, Auto explanation and error handling.
- Inspect `providers list`, `providers estimate`, and `providers smoke-plan` before cloud use.
- Never infer from key presence that a live request is authorized.
- For an approved live test, record exact model/upstream, request count, stream flag, output cap,
  observed latency, returned model, usage source and account charge.
- Remove keys and logs after testing; report only redacted errors.
- Do not report synthetic fixtures or one smoke response as model quality, reliability, savings, or
  routing superiority evidence.
