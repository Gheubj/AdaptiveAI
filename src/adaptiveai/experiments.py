from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def git_revision() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def dependency_versions(
    names: tuple[str, ...] = (
        "numpy",
        "pandas",
        "pyarrow",
        "pydantic",
        "httpx",
        "scikit-learn",
        "scipy",
        "psutil",
        "torch",
    ),
) -> dict[str, str | None]:
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def append_run(
    path: Path,
    *,
    hypothesis: str,
    source_version: str,
    configuration: dict[str, Any],
    seed: int,
    commands: list[str],
    metrics: dict[str, Any],
    errors: list[str],
    conclusion: str,
    input_artifacts: list[dict[str, Any]] | None = None,
    output_artifacts: list[str] | None = None,
    warnings: list[str] | None = None,
    interpretation: str | None = None,
) -> None:
    row = {
        "timestamp": datetime.now(UTC).isoformat(),
        "hypothesis": hypothesis,
        "source_data_version": source_version,
        "configuration": configuration,
        "random_seed": seed,
        "dependency_versions": dependency_versions(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "code_version": git_revision(),
        "commands": commands,
        "input_artifacts": input_artifacts or [],
        "output_artifacts": output_artifacts or [],
        "metrics": metrics,
        "warnings": warnings or [],
        "errors": errors,
        "conclusion": conclusion,
        "interpretation": interpretation or conclusion,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
