from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def sample_archive(tmp_path: Path) -> Path:
    path = tmp_path / "bench-release.tar.gz"
    files = {
        "results/bench/math/test/provider__small/run.json": {
            "performance": 0.5,
            "time_taken": 12.0,
            "records": [
                {
                    "index": 1,
                    "origin_query": "What is 2 + 2?",
                    "prompt": "Answer: 2+2",
                    "prediction": "4",
                    "ground_truth": "4",
                    "score": 1.0,
                    "prompt_tokens": 5,
                    "completion_tokens": 1,
                    "cost": 0.00001,
                },
                {
                    "index": 2,
                    "origin_query": "What is 3 + 3?",
                    "prediction": "5",
                    "ground_truth": "6",
                    "score": 0.0,
                },
            ],
        },
        "results/bench/math/test/provider__strong/run.json": {
            "performance": 1.0,
            "time_taken": 20.0,
            "records": [
                {
                    "index": 1,
                    "origin_query": "What is 2 + 2?",
                    "prediction": "4",
                    "ground_truth": "4",
                    "score": 1.0,
                },
                {
                    "index": 2,
                    "origin_query": "What is 3 + 3?",
                    "prediction": "6",
                    "ground_truth": "6",
                    "score": 1.0,
                },
                {"index": 3, "origin_query": "  ", "score": 0.0},
            ],
        },
    }
    with tarfile.open(path, "w:gz") as archive:
        for name, value in files.items():
            data = json.dumps(value).encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path
