from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from adaptiveai.hardware_routing import RoutingConstraints, route_hardware_aware
from adaptiveai.local_backend import InferenceParameters


class Phase4Service:
    def __init__(self, backend, estimates):
        self.backend, self.estimates = backend, estimates

    def models(self):
        return [
            {"id": model.model_id, "provider": "local", "family": model.family}
            for model in self.backend.list_models()
        ]

    def route(self, payload):
        constraints = RoutingConstraints(
            local_only=payload.get("local_only", True),
            available_memory_bytes=payload.get("available_memory_bytes"),
            max_p95_latency=payload.get("max_p95_latency"),
            max_expected_cost=payload.get("max_expected_cost"),
            preference=payload.get("preference", "quality"),
        )
        decision = route_hardware_aware(
            self.estimates, constraints, policy=payload.get("policy", "hardware_aware")
        )
        return {
            "model": decision.model_id,
            "policy": decision.policy,
            "provenance": decision.provenance,
        }

    def chat(self, payload):
        messages = payload["messages"]
        prompt = "\n".join(str(message["content"]) for message in messages)
        decision = self.route(payload)
        result = self.backend.infer(
            decision["model"],
            prompt,
            InferenceParameters(max_tokens=int(payload.get("max_tokens", 64))),
            timeout=float(payload.get("timeout", 120)),
        )
        return {
            "id": result.request_id,
            "object": "chat.completion",
            "model": result.model_id,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": result.text}}],
            "routing": decision,
            "observed": {
                "latency_seconds": result.elapsed_seconds,
                "generated_tokens": result.generated_tokens,
            },
        }


def make_handler(service):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"status": "ok"})
            elif self.path == "/v1/models":
                self._send(200, {"data": service.models()})
            else:
                self._send(404, {"error": "not_found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length))
                if self.path == "/v1/route":
                    self._send(200, service.route(payload))
                elif self.path == "/v1/chat/completions":
                    self._send(200, service.chat(payload))
                else:
                    self._send(404, {"error": "not_found"})
            except (ValueError, KeyError, RuntimeError) as error:
                self._send(400, {"error": type(error).__name__, "message": str(error)})

        def log_message(self, _format, *_args):
            return

    return Handler


def serve(service, host: str = "127.0.0.1", port: int = 8088) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Public binding requires an explicit external deployment configuration")
    ThreadingHTTPServer((host, port), make_handler(service)).serve_forever()
