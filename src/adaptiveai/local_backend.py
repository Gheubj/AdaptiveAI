from __future__ import annotations

import hashlib
import json
import subprocess
import time
import uuid
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx


@dataclass(frozen=True)
class LocalModel:
    model_id: str
    path: Path
    family: str
    parameters: int
    quantization: str
    license: str
    context_length: int
    file_sha256: str | None = None

    def with_hash(self) -> LocalModel:
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return LocalModel(**{**asdict(self), "file_sha256": digest})


@dataclass(frozen=True)
class InferenceParameters:
    max_tokens: int = 64
    temperature: float = 0.0
    seed: int = 3407
    threads: int = 6
    context_length: int = 2048


@dataclass(frozen=True)
class InferenceResult:
    request_id: str
    model_id: str
    text: str
    elapsed_seconds: float
    prompt_tokens: int | None
    generated_tokens: int | None
    tokens_per_second: float | None
    backend: str
    raw_stderr: str
    ttft_seconds: float | None = None


class BackendError(RuntimeError):
    pass


class LlamaCppBackend:
    def __init__(self, executable: Path, models: tuple[LocalModel, ...]):
        if not executable.exists():
            raise BackendError(f"llama.cpp executable unavailable: {executable}")
        self.executable = executable
        self.models = {model.model_id: model for model in models}

    def list_models(self) -> tuple[LocalModel, ...]:
        return tuple(self.models.values())

    def infer(
        self,
        model_id: str,
        prompt: str,
        parameters: InferenceParameters = InferenceParameters(),
        *,
        timeout: float = 120,
    ) -> InferenceResult:
        if model_id not in self.models:
            raise BackendError(f"Unknown local model: {model_id}")
        model = self.models[model_id]
        command = [
            str(self.executable),
            "-m",
            str(model.path),
            "-p",
            prompt,
            "-n",
            str(parameters.max_tokens),
            "--temp",
            str(parameters.temperature),
            "--seed",
            str(parameters.seed),
            "-t",
            str(parameters.threads),
            "-c",
            str(parameters.context_length),
            "--no-display-prompt",
            "--simple-io",
        ]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, check=False
            )
        except subprocess.TimeoutExpired as error:
            raise BackendError(f"Inference timed out after {timeout}s") from error
        elapsed = time.perf_counter() - started
        if completed.returncode:
            raise BackendError(completed.stderr[-2000:] or f"llama.cpp exit {completed.returncode}")
        generated, rate = _parse_timings(completed.stderr)
        return InferenceResult(
            request_id=str(uuid.uuid4()),
            model_id=model_id,
            text=completed.stdout.strip(),
            elapsed_seconds=elapsed,
            prompt_tokens=None,
            generated_tokens=generated,
            tokens_per_second=rate,
            backend="llama.cpp",
            raw_stderr=completed.stderr,
        )

    def stream(
        self, model_id: str, prompt: str, parameters: InferenceParameters = InferenceParameters()
    ) -> Iterator[str]:
        result = self.infer(model_id, prompt, parameters)
        yield result.text


def _parse_timings(stderr: str) -> tuple[int | None, float | None]:
    generated, rate = None, None
    for line in stderr.splitlines():
        if "eval time" in line and "tokens" in line:
            parts = line.replace("(", " ").replace(")", " ").split()
            for index, item in enumerate(parts):
                if item == "tokens" and index:
                    try:
                        generated = int(parts[index - 1])
                    except ValueError:
                        pass
                if item == "tokens" and index + 2 < len(parts) and parts[index + 1] == "per":
                    try:
                        rate = float(parts[index - 1])
                    except ValueError:
                        pass
    return generated, rate


def load_registry(path: Path) -> tuple[LocalModel, ...]:
    payload = json.loads(path.read_text())
    return tuple(LocalModel(path=Path(row.pop("path")), **row) for row in payload["models"])


class LlamaCppServer:
    """Single-model localhost server with explicit lifecycle and no external prompt transport."""

    def __init__(self, executable: Path, model: LocalModel, *, port: int = 18080, threads: int = 6):
        self.executable, self.model, self.port, self.threads = executable, model, port, threads
        self.process: subprocess.Popen[str] | None = None
        self.load_seconds: float | None = None

    def start(self, timeout: float = 60) -> float:
        if self.process and self.process.poll() is None:
            return 0.0
        started = time.perf_counter()
        self.process = subprocess.Popen(
            [
                str(self.executable),
                "-m",
                str(self.model.path),
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "-t",
                str(self.threads),
                "-c",
                "2048",
                "--metrics",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                error = self.process.stderr.read() if self.process.stderr else ""
                raise BackendError(f"llama-server failed: {error[-2000:]}")
            try:
                if httpx.get(f"http://127.0.0.1:{self.port}/health", timeout=1).status_code == 200:
                    self.load_seconds = time.perf_counter() - started
                    return self.load_seconds
            except httpx.HTTPError:
                time.sleep(0.1)
        self.stop()
        raise BackendError(f"llama-server did not become ready within {timeout}s")

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(5)
        self.process = None

    def infer(
        self, prompt: str, parameters: InferenceParameters, *, timeout: float = 120
    ) -> InferenceResult:
        if not self.process or self.process.poll() is not None:
            raise BackendError("llama-server is not running")
        payload = {
            "model": self.model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": parameters.temperature,
            "seed": parameters.seed,
            "max_tokens": parameters.max_tokens,
            "stream": False,
        }
        started = time.perf_counter()
        try:
            response = httpx.post(
                f"http://127.0.0.1:{self.port}/v1/chat/completions", json=payload, timeout=timeout
            )
        except httpx.TimeoutException as error:
            raise BackendError(f"Inference timed out after {timeout}s") from error
        except httpx.HTTPError as error:
            raise BackendError(f"llama-server request failed: {error}") from error
        elapsed = time.perf_counter() - started
        if response.status_code != 200:
            raise BackendError(f"llama-server HTTP {response.status_code}: {response.text[:1000]}")
        body = response.json()
        usage = body.get("usage", {})
        generated = usage.get("completion_tokens")
        timings = body.get("timings", {})
        return InferenceResult(
            request_id=str(uuid.uuid4()),
            model_id=self.model.model_id,
            text=body["choices"][0]["message"]["content"],
            elapsed_seconds=elapsed,
            prompt_tokens=usage.get("prompt_tokens"),
            generated_tokens=generated,
            tokens_per_second=timings.get("predicted_per_second"),
            backend="llama.cpp-server",
            raw_stderr="",
        )

    def infer_stream_metrics(
        self, prompt: str, parameters: InferenceParameters, *, timeout: float = 120
    ) -> InferenceResult:
        if not self.process or self.process.poll() is not None:
            raise BackendError("llama-server is not running")
        payload = {
            "model": self.model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": parameters.temperature,
            "seed": parameters.seed,
            "max_tokens": parameters.max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        started = time.perf_counter()
        first_token_at = None
        pieces, usage = [], {}
        try:
            with httpx.stream(
                "POST",
                f"http://127.0.0.1:{self.port}/v1/chat/completions",
                json=payload,
                timeout=timeout,
            ) as response:
                if response.status_code != 200:
                    raise BackendError(
                        f"llama-server HTTP {response.status_code}: {response.read()[:1000]}"
                    )
                for line in response.iter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    body = json.loads(line[6:])
                    usage = body.get("usage") or usage
                    choices = body.get("choices") or []
                    content = choices[0].get("delta", {}).get("content", "") if choices else ""
                    if content:
                        if first_token_at is None:
                            first_token_at = time.perf_counter()
                        pieces.append(content)
        except httpx.TimeoutException as error:
            raise BackendError(f"Inference timed out after {timeout}s") from error
        except httpx.HTTPError as error:
            raise BackendError(f"llama-server request failed: {error}") from error
        elapsed = time.perf_counter() - started
        generated = usage.get("completion_tokens")
        decode_seconds = elapsed - (first_token_at - started) if first_token_at else None
        rate = (
            generated / decode_seconds
            if generated and decode_seconds and decode_seconds > 0
            else None
        )
        return InferenceResult(
            request_id=str(uuid.uuid4()),
            model_id=self.model.model_id,
            text="".join(pieces),
            elapsed_seconds=elapsed,
            prompt_tokens=usage.get("prompt_tokens"),
            generated_tokens=generated,
            tokens_per_second=rate,
            backend="llama.cpp-server",
            raw_stderr="",
            ttft_seconds=(first_token_at - started) if first_token_at else None,
        )

    def stream_events(
        self, prompt: str, parameters: InferenceParameters, *, timeout: float = 120
    ) -> Iterator[dict[str, object]]:
        """Yield normalized content/usage events from llama.cpp's OpenAI-compatible stream."""
        if not self.process or self.process.poll() is not None:
            raise BackendError("llama-server is not running")
        payload = {
            "model": self.model.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": parameters.temperature,
            "seed": parameters.seed,
            "max_tokens": parameters.max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        try:
            with httpx.stream(
                "POST",
                f"http://127.0.0.1:{self.port}/v1/chat/completions",
                json=payload,
                timeout=timeout,
            ) as response:
                if response.status_code != 200:
                    raise BackendError(
                        f"llama-server HTTP {response.status_code}: {response.read()[:1000]}"
                    )
                for line in response.iter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    body = json.loads(line[6:])
                    choices = body.get("choices") or []
                    content = choices[0].get("delta", {}).get("content", "") if choices else ""
                    usage = body.get("usage")
                    if content:
                        yield {"type": "content", "content": content}
                    if usage:
                        yield {"type": "usage", "usage": usage}
        except httpx.TimeoutException as error:
            raise BackendError(f"Inference timed out after {timeout}s") from error
        except httpx.HTTPError as error:
            raise BackendError(f"llama-server request failed: {error}") from error

    def __enter__(self) -> LlamaCppServer:
        self.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.stop()
