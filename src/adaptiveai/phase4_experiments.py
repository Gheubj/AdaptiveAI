# ruff: noqa: E501
from __future__ import annotations

import random
import re
from pathlib import Path

import pandas as pd
import psutil

from adaptiveai.hardware_routing import (
    ModelEstimate,
    RoutingConstraints,
    route_hardware_aware,
)
from adaptiveai.local_backend import InferenceParameters, LlamaCppServer, LocalModel
from adaptiveai.routers import TfidfSuccessRouter


def quality_panel() -> pd.DataFrame:
    """Original objective micro-panel, Apache-2.0, frozen before model execution."""
    rows = [
        ("tr01", "train", "math", "Return only the integer: 17 + 28", "45"),
        ("tr02", "train", "math", "Return only the integer: 9 * 7", "63"),
        ("tr03", "train", "factual", "Return only the capital of Japan.", "tokyo"),
        ("tr04", "train", "factual", "Return only the chemical symbol for gold.", "au"),
        (
            "tr05",
            "train",
            "extract",
            "Extract only the email: Contact Ana at ana@example.org today.",
            "ana@example.org",
        ),
        (
            "tr06",
            "train",
            "extract",
            "Return only the order ID: status for order ZX-204 is ready.",
            "zx-204",
        ),
        (
            "tr07",
            "train",
            "instruction",
            "Output exactly three comma-separated colors: red, green, blue",
            "red,green,blue",
        ),
        ("tr08", "train", "instruction", "Output exactly the lowercase word: HELLO", "hello"),
        ("va01", "validation", "math", "Return only the integer: 144 / 12", "12"),
        ("va02", "validation", "math", "Return only the integer: 35 - 19", "16"),
        (
            "va03",
            "validation",
            "factual",
            "Return only the largest planet in the Solar System.",
            "jupiter",
        ),
        (
            "va04",
            "validation",
            "factual",
            "Return only the language primarily spoken in Brazil.",
            "portuguese",
        ),
        (
            "va05",
            "validation",
            "extract",
            "Extract only the date: The event is on 2027-04-03.",
            "2027-04-03",
        ),
        (
            "va06",
            "validation",
            "extract",
            "Return only the amount: Invoice total is USD 42.50.",
            "42.50",
        ),
        (
            "va07",
            "validation",
            "instruction",
            "Output exactly two uppercase letters separated by a hyphen: a and b",
            "a-b",
        ),
        (
            "va08",
            "validation",
            "instruction",
            "Output exactly JSON with key ok and boolean true, no spaces.",
            '{"ok":true}',
        ),
        ("te01", "test", "math", "Return only the integer: 23 * 4", "92"),
        ("te02", "test", "math", "Return only the integer: 81 / 9 + 6", "15"),
        ("te03", "test", "factual", "Return only the capital of Canada.", "ottawa"),
        ("te04", "test", "factual", "Return only the chemical symbol for sodium.", "na"),
        (
            "te05",
            "test",
            "extract",
            "Extract only the IPv4 address: server=192.0.2.7 port=443",
            "192.0.2.7",
        ),
        (
            "te06",
            "test",
            "extract",
            "Return only the ticket code: Please resolve ticket AB-771.",
            "ab-771",
        ),
        (
            "te07",
            "test",
            "instruction",
            "Output exactly four digits with no separator: 1 2 3 4",
            "1234",
        ),
        ("te08", "test", "instruction", "Output exactly the word yes in uppercase.", "yes"),
    ]
    return pd.DataFrame(rows, columns=["query_id", "split", "task", "prompt", "answer"])


def normalize_answer(text: str) -> str:
    return re.sub(r"[\s`'\".,:;]+", "", text.strip().lower())


def score_answer(output: str, answer: str) -> float:
    return float(normalize_answer(output) == normalize_answer(answer))


def run_quality(models: tuple[LocalModel, ...], server_binary: Path, output: Path) -> pd.DataFrame:
    panel = quality_panel()
    output.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output / "quality_panel_frozen.parquet", index=False)
    rows = []
    parameters = InferenceParameters(max_tokens=32, temperature=0, seed=3407, threads=6)
    for model_index, model in enumerate(models):
        with LlamaCppServer(server_binary, model, port=18100 + model_index) as server:
            for record in panel.itertuples(index=False):
                result = server.infer(record.prompt, parameters)
                rows.append(
                    {
                        "query_id": record.query_id,
                        "split": record.split,
                        "task": record.task,
                        "model_id": model.model_id,
                        "output": result.text,
                        "success": score_answer(result.text, record.answer),
                        "latency_seconds": result.elapsed_seconds,
                        "prompt_tokens": result.prompt_tokens,
                        "generated_tokens": result.generated_tokens,
                        "tokens_per_second": result.tokens_per_second,
                        "load_seconds": server.load_seconds,
                    }
                )
    frame = pd.DataFrame(rows)
    frame.to_parquet(output / "local_quality_outputs.parquet", index=False)
    return frame


def run_profile(models: tuple[LocalModel, ...], server_binary: Path, output: Path) -> pd.DataFrame:
    prompts = {
        "short": "Reply with one word: ready",
        "medium": "In two short sentences, explain why the sky appears blue during daytime.",
        "long": "Summarize the following constraints in three bullets: local inference must remain private, fit available memory, respect a latency budget, log provenance, and never use post-execution features for routing.",
    }
    rows = []
    process = psutil.Process()
    for model_index, model in enumerate(models):
        for cold_repeat in range(3):
            server = LlamaCppServer(server_binary, model, port=18200 + model_index)
            available_before = psutil.virtual_memory().available
            load = server.start()
            child = psutil.Process(server.process.pid) if server.process else process
            result = server.infer_stream_metrics(
                prompts["short"], InferenceParameters(max_tokens=16)
            )
            rows.append(
                {
                    "model_id": model.model_id,
                    "state": "cold_process",
                    "workload": "short",
                    "repeat": cold_repeat,
                    "load_seconds": load,
                    "latency_seconds": result.elapsed_seconds,
                    "tokens_per_second": result.tokens_per_second,
                    "rss_bytes": child.memory_info().rss,
                    "available_ram_before": available_before,
                    "generated_tokens": result.generated_tokens,
                    "ttft_seconds": result.ttft_seconds,
                }
            )
            server.stop()
        with LlamaCppServer(server_binary, model, port=18300 + model_index) as server:
            server.infer(prompts["short"], InferenceParameters(max_tokens=8))
            for workload, prompt in prompts.items():
                for repeat in range(10):
                    result = server.infer_stream_metrics(prompt, InferenceParameters(max_tokens=32))
                    child = psutil.Process(server.process.pid) if server.process else process
                    rows.append(
                        {
                            "model_id": model.model_id,
                            "state": "warm",
                            "workload": workload,
                            "repeat": repeat,
                            "load_seconds": 0.0,
                            "latency_seconds": result.elapsed_seconds,
                            "tokens_per_second": result.tokens_per_second,
                            "rss_bytes": child.memory_info().rss,
                            "available_ram_before": psutil.virtual_memory().available,
                            "generated_tokens": result.generated_tokens,
                            "ttft_seconds": result.ttft_seconds,
                        }
                    )
    frame = pd.DataFrame(rows)
    frame.to_parquet(output / "raw_hardware_profile.parquet", index=False)
    return frame


def evaluate_policies(quality: pd.DataFrame, profile: pd.DataFrame, output: Path) -> pd.DataFrame:
    models = tuple(sorted(quality.model_id.unique()))
    training = quality[quality.split.isin(["train", "validation"])]
    test = quality[quality.split == "test"]
    quality_by_model = training.groupby("model_id").success.mean().to_dict()
    quality_by_task = training.groupby(["task", "model_id"]).success.mean().to_dict()
    latency = (
        profile[(profile.state == "warm") & (profile.workload == "short")]
        .groupby("model_id")
        .latency_seconds.quantile(0.95)
        .to_dict()
    )
    memory = profile.groupby("model_id").rss_bytes.max().to_dict()
    estimates = tuple(
        ModelEstimate(model, "local", quality_by_model[model], latency[model], int(memory[model]))
        for model in models
    )
    fastest = min(models, key=latency.get)
    strongest = max(models, key=lambda model: quality_by_model[model])
    tfidf = TfidfSuccessRouter(seed=3407)
    panel = quality_panel().set_index("query_id")
    train_ids = sorted(training.query_id.unique())
    tfidf.fit(
        [panel.loc[q].prompt for q in train_ids],
        {
            model: training[training.model_id == model]
            .set_index("query_id")
            .reindex(train_ids)
            .success.to_numpy()
            for model in models
        },
    )
    rows = []
    rng = random.Random(3407)
    for query_id, group in test.groupby("query_id"):
        task, prompt = panel.loc[query_id, ["task", "prompt"]]
        choices = {
            "fixed_fastest": fastest,
            "fixed_strongest": strongest,
            "random": rng.choice(models),
            "quality_only": max(
                models,
                key=lambda model: quality_by_task.get((task, model), quality_by_model[model]),
            ),
            "tfidf_quality": max(
                tfidf.predict_utilities(prompt, models),
                key=tfidf.predict_utilities(prompt, models).get,
            ),
            "latency_aware": route_hardware_aware(
                estimates, RoutingConstraints(preference="latency"), policy="fixed_fastest"
            ).model_id,
            "memory_aware": min(models, key=memory.get),
            "hardware_aware": route_hardware_aware(
                estimates,
                RoutingConstraints(
                    max_p95_latency=max(latency.values()),
                    available_memory_bytes=int(psutil.virtual_memory().available),
                ),
            ).model_id,
        }
        indexed = group.set_index("model_id")
        for policy, model in choices.items():
            row = indexed.loc[model]
            rows.append(
                {
                    "query_id": query_id,
                    "policy": policy,
                    "selected_model_id": model,
                    "success": row.success,
                    "latency_seconds": row.latency_seconds,
                    "rss_bytes": memory[model],
                    "failed": False,
                }
            )
    result = pd.DataFrame(rows)
    result.to_parquet(output / "policy_decisions.parquet", index=False)
    return result
