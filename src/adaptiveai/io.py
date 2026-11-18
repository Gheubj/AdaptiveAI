from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tarfile
from collections.abc import Iterator
from pathlib import Path

import httpx

from adaptiveai import __version__
from adaptiveai.schemas import SourceManifest

LOGGER = logging.getLogger(__name__)


class ArchiveError(ValueError):
    pass


OFFICIAL_ARCHIVE_URL = (
    "https://huggingface.co/datasets/NPULH/LLMRouterBench/resolve/main/bench-release.tar.gz"
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def import_archive(
    source: Path,
    raw_root: Path,
    source_id: str = "NPULH/LLMRouterBench",
    source_uri: str = "local-file",
    original_filename: str | None = None,
) -> tuple[Path, SourceManifest]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if not tarfile.is_tarfile(source):
        raise ArchiveError(f"Not a readable tar archive: {source}")
    digest = sha256_file(source)
    destination = raw_root / source_id.replace("/", "__") / digest
    destination.mkdir(parents=True, exist_ok=True)
    filename = original_filename or source.name
    copied = destination / filename
    if not copied.exists():
        shutil.copy2(source, copied)
    manifest = SourceManifest(
        source_id=source_id,
        source_uri=source_uri,
        original_filename=filename,
        size_bytes=source.stat().st_size,
        sha256=digest,
        importer_version=__version__,
    )
    (destination / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return copied, manifest


def download_official_archive(
    raw_root: Path,
    *,
    url: str = OFFICIAL_ARCHIVE_URL,
    max_bytes: int = 3 * 1024**3,
    max_retries: int = 50,
    transport: httpx.BaseTransport | None = None,
) -> tuple[Path, SourceManifest]:
    """Explicitly download the official archive with HTTP Range resume support."""
    raw_root.mkdir(parents=True, exist_ok=True)
    source_root = raw_root / "NPULH__LLMRouterBench"
    for manifest_path in source_root.glob("*/manifest.json"):
        try:
            manifest = SourceManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
            candidate = manifest_path.parent / manifest.original_filename
            if (
                manifest.source_uri == url
                and candidate.is_file()
                and candidate.stat().st_size == manifest.size_bytes
                and sha256_file(candidate) == manifest.sha256
                and tarfile.is_tarfile(candidate)
            ):
                return candidate, manifest
        except (OSError, ValueError):
            continue

    staging = raw_root / ".downloads"
    staging.mkdir(parents=True, exist_ok=True)
    temporary_path = staging / "bench-release.tar.gz.part"
    with httpx.Client(timeout=120, follow_redirects=True, transport=transport) as client:
        for attempt in range(max_retries + 1):
            offset = temporary_path.stat().st_size if temporary_path.exists() else 0
            if offset > max_bytes:
                raise ArchiveError(f"Partial archive exceeds {max_bytes} bytes")
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            try:
                with client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    resumed = offset > 0 and response.status_code == 206
                    if offset and not resumed:
                        offset = 0
                    declared = int(response.headers.get("content-length", 0))
                    if offset + declared > max_bytes:
                        raise ArchiveError(f"Declared archive size exceeds {max_bytes} bytes")
                    mode = "ab" if resumed else "wb"
                    total = offset
                    with temporary_path.open(mode) as temporary:
                        for chunk in response.iter_bytes(1024 * 1024):
                            total += len(chunk)
                            if total > max_bytes:
                                raise ArchiveError(f"Downloaded archive exceeds {max_bytes} bytes")
                            temporary.write(chunk)
                break
            except httpx.TransportError:
                if attempt >= max_retries:
                    raise
                LOGGER.warning(
                    "Download interrupted after %d bytes; resuming (%d/%d)",
                    temporary_path.stat().st_size,
                    attempt + 1,
                    max_retries,
                )
    try:
        return import_archive(
            temporary_path,
            raw_root,
            source_uri=url,
            original_filename="bench-release.tar.gz",
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def _safe_members(archive: tarfile.TarFile) -> Iterator[tarfile.TarInfo]:
    for member in archive:
        parts = Path(member.name).parts
        if member.issym() or member.islnk() or Path(member.name).is_absolute() or ".." in parts:
            raise ArchiveError(f"Unsafe archive member: {member.name}")
        yield member


def iter_json_documents(archive_path: Path) -> Iterator[tuple[str, dict]]:
    try:
        with tarfile.open(archive_path, "r:*") as archive:
            for member in _safe_members(archive):
                if not member.isfile() or not member.name.lower().endswith(".json"):
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    continue
                try:
                    value = json.load(stream)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ArchiveError(f"Invalid JSON in {member.name}: {exc}") from exc
                if not isinstance(value, dict):
                    raise ArchiveError(f"Expected JSON object in {member.name}")
                yield member.name, value
    except (tarfile.TarError, OSError) as exc:
        raise ArchiveError(f"Cannot read {archive_path}: {exc}") from exc
