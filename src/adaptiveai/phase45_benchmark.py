from __future__ import annotations

import json
import math
import random
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
import pandas as pd

from adaptiveai.local_backend import BackendError, InferenceParameters, LlamaCppServer, LocalModel

GENERATOR_VERSION = "phase45-v1"
SEED = 3407


FACTS = (
    ("capital of Canada", "Ottawa"),
    ("capital of Japan", "Tokyo"),
    ("capital of Australia", "Canberra"),
    ("capital of Brazil", "Brasilia"),
    ("capital of Kenya", "Nairobi"),
    ("chemical symbol for gold", "Au"),
    ("chemical symbol for sodium", "Na"),
    ("chemical symbol for iron", "Fe"),
    ("largest planet in the Solar System", "Jupiter"),
    ("smallest prime number", "2"),
    ("language primarily spoken in Brazil", "Portuguese"),
    ("ocean between Africa and Australia", "Indian Ocean"),
    ("author of Pride and Prejudice", "Jane Austen"),
    ("planet known as the Red Planet", "Mars"),
    ("gas plants absorb during photosynthesis", "carbon dioxide"),
    ("currency of Japan", "yen"),
    ("number of sides in a hexagon", "6"),
    ("freezing point of water in Celsius", "0"),
)


@dataclass(frozen=True)
class ScoreResult:
    correct: bool
    normalized_prediction: str | None
    status: str


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold().strip()
    return re.sub(r"[^\w@.\-]+", " ", text).strip(" .")


def _final_fragment(text: str) -> str:
    cleaned = text.strip().strip("`")
    tagged = re.findall(
        r"(?:final answer|answer|result|output)\s*(?:is|:|=)\s*([^\n]+)",
        cleaned,
        flags=re.I,
    )
    return tagged[-1].strip() if tagged else cleaned.splitlines()[-1].strip()


def _number(text: str) -> Decimal | None:
    fragment = _final_fragment(text).replace(",", "")
    full = re.fullmatch(r"[\s$]*([-+]?\d+(?:\.\d+)?)(?:\s*%?)?[.!]?\s*", fragment)
    if full:
        try:
            return Decimal(full.group(1))
        except InvalidOperation:
            return None
    # Frozen allowance for a single numeric value in a short answer sentence. Multiple values are
    # ambiguous and intentionally rejected, preventing distractor-number containment scoring.
    values = re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?![\w.])", fragment)
    if len(values) == 1 and len(fragment.split()) <= 10:
        try:
            return Decimal(values[0])
        except InvalidOperation:
            return None
    return None


def score_response(output: str, reference: str, answer_type: str) -> ScoreResult:
    if not output.strip():
        return ScoreResult(False, None, "empty")
    if answer_type == "number":
        predicted = _number(output)
        if predicted is None:
            return ScoreResult(False, None, "unscorable")
        target = Decimal(reference)
        tolerance = max(Decimal("0.000001"), abs(target) * Decimal("0.000001"))
        return ScoreResult(abs(predicted - target) <= tolerance, str(predicted), "scored")
    if answer_type == "json":
        matches = re.findall(r"\{[^{}]*\}", output, flags=re.S)
        if len(matches) != 1:
            return ScoreResult(False, None, "unscorable")
        try:
            predicted, target = json.loads(matches[0]), json.loads(reference)
        except (ValueError, TypeError):
            return ScoreResult(False, None, "unscorable")
        if not isinstance(predicted, dict) or set(predicted) != set(target):
            return ScoreResult(False, json.dumps(predicted, sort_keys=True), "scored")
        normalized = json.dumps(predicted, sort_keys=True, separators=(",", ":"))
        expected = json.dumps(target, sort_keys=True, separators=(",", ":"))
        return ScoreResult(normalized == expected, normalized, "scored")
    fragment = _plain(_final_fragment(output))
    target = _plain(reference)
    return ScoreResult(fragment == target, fragment, "scored")


def scorer_validation_cases() -> pd.DataFrame:
    cases = [
        ("42", "42", "number", True),
        ("The final answer is 42.", "42", "number", True),
        ("I considered 40. The answer is 42.", "42", "number", True),
        ("It is either 41 or 42", "42", "number", False),
        ("The answer is 41, not 42", "42", "number", False),
        ("Answer: 3.500000", "3.5", "number", True),
        ("Ottawa.", "ottawa", "text", True),
        ("Canada has provinces. Answer: Ottawa", "Ottawa", "text", True),
        ("Toronto or Ottawa", "Ottawa", "text", False),
        ('```json\n{"id":"AB-7","amount":3}\n```', '{"id":"AB-7","amount":3}', "json", True),
        ('{"id":"AB-7","amount":4}', '{"id":"AB-7","amount":3}', "json", False),
        ('{"id":"AB-7"}', '{"id":"AB-7","amount":3}', "json", False),
        ('{"id":"AB-7"} or {"id":"AB-8"}', '{"id":"AB-7"}', "json", False),
        ("", "yes", "text", False),
    ]
    rows = []
    for output, reference, answer_type, expected in cases:
        result = score_response(output, reference, answer_type)
        rows.append(
            {
                "output": output,
                "reference": reference,
                "answer_type": answer_type,
                "expected": expected,
                "observed": result.correct,
                "status": result.status,
            }
        )
    return pd.DataFrame(rows)


def _task_row(task: str, index: int, rng: random.Random) -> tuple[str, str, str]:
    if task == "math":
        a, b = rng.randint(7, 99), rng.randint(2, 31)
        operation = index % 4
        if operation == 0:
            return f"Compute {a} + {b}. Give the final number only.", str(a + b), "number"
        if operation == 1:
            return f"Compute {a} - {b}. Give the final number only.", str(a - b), "number"
        if operation == 2:
            b = rng.randint(2, 12)
            return f"Compute {a} * {b}. Give the final number only.", str(a * b), "number"
        quotient, divisor = rng.randint(2, 30), rng.randint(2, 12)
        return (
            f"Compute {quotient * divisor} / {divisor}. Give the final number only.",
            str(quotient),
            "number",
        )
    if task == "factual":
        subject, answer = FACTS[index % len(FACTS)]
        return f"What is the {subject}? Give only the answer.", answer, "text"
    if task == "extraction":
        order = f"ZX-{100 + index}"
        amount = (index % 90) + 10
        prompt = (
            f'Read: "customer C{index:03d}; order {order}; total {amount}; status ready". '
            "Return one JSON object with exactly keys order and amount; amount must be an integer."
        )
        return prompt, json.dumps({"order": order, "amount": amount}), "json"
    if task == "instruction":
        words = ["amber", "cedar", "delta", "pixel", "river", "stone"]
        word = words[index % len(words)]
        count = 2 + index % 3
        return (
            f"Output exactly {count} copies of {word.upper()}, separated by a single hyphen.",
            "-".join([word] * count),
            "text",
        )
    if task == "programming":
        start, increment = rng.randint(1, 20), rng.randint(2, 9)
        loops = 2 + index % 5
        prompt = (
            f"Without executing code, give only the printed integer: x={start}; "
            f"for _ in range({loops}): x += {increment}; print(x)"
        )
        return prompt, str(start + loops * increment), "number"
    values = rng.sample(range(10, 100), 4)
    if index % 2:
        return (
            f"Which is the second-smallest number: {', '.join(map(str, values))}? "
            "Give only that number.",
            str(sorted(values)[1]),
            "number",
        )
    start, step = rng.randint(1, 15), rng.randint(2, 8)
    sequence = [start + step * i for i in range(4)]
    return (
        "Continue the arithmetic sequence "
        f"{', '.join(map(str, sequence))}. Give only the next number.",
        str(sequence[-1] + step),
        "number",
    )


def benchmark_v2() -> pd.DataFrame:
    sizes = {"train": 150, "validation": 100, "test": 250}
    tasks = ("math", "factual", "extraction", "instruction", "programming", "reasoning")
    rows = []
    global_index = 0
    for split_index, (split, size) in enumerate(sizes.items()):
        rng = random.Random(SEED + split_index * 100_003)
        for local_index in range(size):
            task = tasks[local_index % len(tasks)]
            prompt, reference, answer_type = _task_row(task, global_index, rng)
            prompt = f"Benchmark item {global_index:04d}. {prompt}"
            rows.append(
                {
                    "query_id": f"p45-{split[:2]}-{local_index:04d}",
                    "split": split,
                    "task": task,
                    "prompt": prompt,
                    "reference": reference,
                    "answer_type": answer_type,
                    "generator_version": GENERATOR_VERSION,
                    "generation_seed": SEED + split_index * 100_003,
                }
            )
            global_index += 1
    frame = pd.DataFrame(rows)
    normalized = frame.prompt.map(_plain)
    if normalized.duplicated().any():
        duplicates = frame.loc[normalized.duplicated(False), "query_id"].tolist()
        raise ValueError(f"Duplicate generated prompts: {duplicates[:5]}")
    return frame


def run_matched_evaluation(
    models: tuple[LocalModel, ...], server_binary: Path, output_dir: Path
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    panel = benchmark_v2()
    panel.to_parquet(output_dir / "benchmark_v2_frozen.parquet", index=False)
    validation = scorer_validation_cases()
    validation.to_parquet(output_dir / "scorer_validation.parquet", index=False)
    if not (validation.expected == validation.observed).all():
        raise RuntimeError("Scorer validation failed; model evaluation refused")

    partial = output_dir / "matched_outputs.partial.jsonl"
    existing: dict[tuple[str, str], dict[str, object]] = {}
    if partial.exists():
        for line in partial.read_text().splitlines():
            row = json.loads(line)
            existing[(row["model_id"], row["query_id"])] = row
    parameters = InferenceParameters(max_tokens=48, temperature=0, seed=SEED, threads=6)
    for model_index, model in enumerate(models):
        with LlamaCppServer(server_binary, model, port=18450 + model_index) as server:
            for record in panel.itertuples(index=False):
                key = (model.model_id, record.query_id)
                if key in existing:
                    continue
                try:
                    result = server.infer_stream_metrics(record.prompt, parameters, timeout=60)
                    score = score_response(result.text, record.reference, record.answer_type)
                    row = {
                        "query_id": record.query_id,
                        "split": record.split,
                        "task": record.task,
                        "model_id": model.model_id,
                        "output": result.text,
                        "normalized_answer": score.normalized_prediction,
                        "correct": float(score.correct),
                        "score_status": score.status,
                        "latency_seconds": result.elapsed_seconds,
                        "ttft_seconds": result.ttft_seconds,
                        "prompt_tokens": result.prompt_tokens,
                        "generated_tokens": result.generated_tokens,
                        "tokens_per_second": result.tokens_per_second,
                        "load_seconds": server.load_seconds,
                        "failure_status": None,
                        "seed": SEED,
                        "temperature": 0.0,
                        "max_tokens": 48,
                    }
                except BackendError as error:
                    row = {
                        "query_id": record.query_id,
                        "split": record.split,
                        "task": record.task,
                        "model_id": model.model_id,
                        "output": "",
                        "normalized_answer": None,
                        "correct": 0.0,
                        "score_status": "backend_failure",
                        "latency_seconds": math.nan,
                        "ttft_seconds": math.nan,
                        "prompt_tokens": None,
                        "generated_tokens": None,
                        "tokens_per_second": None,
                        "load_seconds": server.load_seconds,
                        "failure_status": str(error),
                        "seed": SEED,
                        "temperature": 0.0,
                        "max_tokens": 48,
                    }
                    server.stop()
                    server.start()
                with partial.open("a") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                existing[key] = row
    frame = pd.DataFrame(existing.values()).sort_values(["model_id", "query_id"])
    frame.to_parquet(output_dir / "matched_model_outputs.parquet", index=False)
    return frame


def bootstrap_mean(
    values: np.ndarray, *, seed: int = SEED, draws: int = 5000
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return tuple(float(x) for x in np.quantile(samples, [0.025, 0.975]))
