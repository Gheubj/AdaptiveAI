from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LocalProviderHandler(BaseHTTPRequestHandler):
    """Deterministic localhost OpenAI-compatible provider used for E2E validation."""

    server_version = "AdaptiveAITestProvider/1"

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return self.headers.get("Authorization") == "Bearer local-test-key"

    def do_GET(self) -> None:
        if self.path != "/v1/models":
            self._json(404, {"error": "not_found"})
        elif not self._authorized():
            self._json(401, {"error": "authentication"})
        else:
            self._json(
                200,
                {"object": "list", "data": [{"id": "local-e2e"}, {"id": "fallback"}]},
            )

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._json(404, {"error": "not_found"})
            return
        if not self._authorized():
            self._json(401, {"error": "authentication"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            model = payload["model"]
            content = payload["messages"][-1]["content"]
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            self._json(400, {"error": "invalid_request"})
            return
        if model == "missing":
            self._json(404, {"error": "model_not_found"})
            return
        statuses = {"RATE_LIMIT": 429, "UNAVAILABLE": 503, "INVALID": 400}
        if content in statuses:
            self._json(statuses[content], {"error": content.lower()})
            return
        if content == "READ_TIMEOUT":
            time.sleep(0.2)
        if content == "MALFORMED":
            body = b"not-json"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if content == "OVERSIZED":
            self._json(200, self._completion(model, "x" * 8192))
            return
        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            rows = [
                {"id": "e2e-stream", "choices": [{"delta": {"content": "local "}}]},
                {
                    "id": "e2e-stream",
                    "choices": [{"delta": {"content": "response"}}],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2},
                },
            ]
            try:
                for index, row in enumerate(rows):
                    self.wfile.write(f"data: {json.dumps(row)}\n\n".encode())
                    self.wfile.flush()
                    if content == "INTERRUPTED" and index == 0:
                        return
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return
            return
        response = self._completion(model, "local response")
        if content == "NO_USAGE":
            response.pop("usage")
        self._json(200, response)

    @staticmethod
    def _completion(model: str, text: str) -> dict[str, object]:
        return {
            "id": "e2e-id",
            "object": "chat.completion",
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    def log_message(self, _format: str, *_args: object) -> None:
        return


def make_test_provider(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), LocalProviderHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "localhost", "::1"])
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args(argv)
    server = make_test_provider(args.host, args.port)
    print(f"AdaptiveAI local test provider: http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
