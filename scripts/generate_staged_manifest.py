from __future__ import annotations

import json
import mimetypes
import subprocess
from pathlib import Path


def purpose(path: str) -> str:
    if path.startswith("src/"):
        return "Python package source"
    if path.startswith("tests/"):
        return "Automated test"
    if path.startswith("docs/"):
        return "Public documentation or release audit"
    if path.startswith("examples/"):
        return "Developer example"
    if path.startswith(".github/"):
        return "Continuous integration"
    if path.startswith("data/"):
        return "Small model registry/profile metadata; no weights"
    if path.startswith("experiments/"):
        return "Aggregate experiment provenance; no row-level dataset"
    if path.startswith("references/"):
        return "Bibliography metadata"
    if path.startswith("scripts/"):
        return "Release/audit utility"
    return "Project, packaging, license, or release metadata"


def main() -> None:
    names = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    rows = []
    for name in sorted(set(names) | {"docs/STAGED_FILE_MANIFEST.json"}):
        path = Path(name)
        if not path.is_file() and name != "docs/STAGED_FILE_MANIFEST.json":
            continue
        size = path.stat().st_size if path.exists() else 0
        mime = mimetypes.guess_type(name)[0] or "text/plain"
        rows.append(
            {
                "path": name,
                "size_bytes": size,
                "file_type": mime,
                "purpose": purpose(name),
                "publication_suitability": "include",
            }
        )
    output = Path("docs/STAGED_FILE_MANIFEST.json")
    # The manifest includes itself. Iterate until the serialized self-size reaches a fixed point.
    for _ in range(10):
        output.write_text(json.dumps({"files": rows}, indent=2) + "\n")
        size = output.stat().st_size
        self_row = next(row for row in rows if row["path"] == str(output))
        if self_row["size_bytes"] == size:
            break
        self_row["size_bytes"] = size
    else:
        raise RuntimeError("manifest self-size did not stabilize")


if __name__ == "__main__":
    main()
