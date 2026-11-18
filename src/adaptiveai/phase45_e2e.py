from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import psutil

from adaptiveai.local_backend import InferenceParameters, LlamaCppServer, load_registry
from adaptiveai.phase45_benchmark import SEED, score_response


def run_policy_execution(
    panel_path: Path,
    registry_path: Path,
    server_binary: Path,
    output_path: Path,
) -> pd.DataFrame:
    panel = pd.read_parquet(panel_path)
    selected = (
        panel[panel.split == "test"].groupby("task", sort=True).head(4).sort_values("query_id")
    )
    models = {model.model_id: model for model in load_registry(registry_path)}
    fastest = "qwen2.5-0.5b-instruct-q4km"
    strongest = "smollm2-1.7b-instruct-q4km"
    task_models = {
        "extraction": fastest,
        "factual": strongest,
        "instruction": strongest,
        "math": strongest,
        "programming": fastest,
        "reasoning": strongest,
    }
    policies = {
        "fixed_fastest": lambda _row: fastest,
        "fixed_strongest": lambda _row: strongest,
        "task_aware": lambda row: task_models[row.task],
        "hardware_aware": lambda _row: strongest,
    }
    parameters = InferenceParameters(max_tokens=48, temperature=0, seed=SEED, threads=6)
    rows = []
    for policy, route in policies.items():
        server: LlamaCppServer | None = None
        loaded_model = None
        try:
            for record in selected.itertuples(index=False):
                route_started = time.perf_counter()
                model_id = route(record)
                router_seconds = time.perf_counter() - route_started
                switched = loaded_model is not None and loaded_model != model_id
                cold = loaded_model is None
                load_seconds = 0.0
                if loaded_model != model_id:
                    if server is not None:
                        server.stop()
                    server = LlamaCppServer(server_binary, models[model_id], port=18580)
                    load_seconds = server.start()
                    loaded_model = model_id
                assert server is not None and server.process is not None
                result = server.infer_stream_metrics(record.prompt, parameters, timeout=60)
                score = score_response(result.text, record.reference, record.answer_type)
                rss = psutil.Process(server.process.pid).memory_info().rss
                rows.append(
                    {
                        "query_id": record.query_id,
                        "task": record.task,
                        "policy": policy,
                        "selected_model_id": model_id,
                        "correct": float(score.correct),
                        "latency_seconds": result.elapsed_seconds,
                        "ttft_seconds": result.ttft_seconds,
                        "router_seconds": router_seconds,
                        "load_seconds": load_seconds,
                        "end_to_end_with_load_seconds": result.elapsed_seconds + load_seconds,
                        "tokens_per_second": result.tokens_per_second,
                        "generated_tokens": result.generated_tokens,
                        "rss_bytes": rss,
                        "cold_start": cold,
                        "model_switch": switched,
                        "failure_status": None,
                    }
                )
        finally:
            if server is not None:
                server.stop()
    frame = pd.DataFrame(rows)
    frame.to_parquet(output_path, index=False)
    return frame
