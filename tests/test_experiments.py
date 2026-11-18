import json
from pathlib import Path

from adaptiveai.experiments import append_run


def test_run_log_is_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "runs.jsonl"
    append_run(
        path,
        hypothesis="h",
        source_version="sha",
        configuration={},
        seed=1,
        commands=["pytest"],
        metrics={"passed": 1},
        errors=[],
        conclusion="ok",
        input_artifacts=[{"path": "input", "sha256": "abc"}],
        output_artifacts=["output"],
        warnings=["warning"],
        interpretation="test-only",
    )
    row = json.loads(path.read_text())
    assert row["random_seed"] == 1
    assert row["commands"] == ["pytest"]
    assert row["environment"]["python"]
    assert row["input_artifacts"][0]["sha256"] == "abc"
