import io
import tarfile
from pathlib import Path

import httpx
import pytest

from adaptiveai.io import (
    ArchiveError,
    download_official_archive,
    import_archive,
    iter_json_documents,
    sha256_file,
)


def test_import_preserves_bytes_and_writes_manifest(sample_archive: Path, tmp_path: Path) -> None:
    copied, manifest = import_archive(sample_archive, tmp_path / "raw")
    assert copied.read_bytes() == sample_archive.read_bytes()
    assert manifest.sha256 == sha256_file(sample_archive)
    assert manifest.size_bytes == sample_archive.stat().st_size
    assert (copied.parent / "manifest.json").exists()


def test_corrupt_archive_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.tar.gz"
    bad.write_bytes(b"not a tar")
    with pytest.raises(ArchiveError):
        import_archive(bad, tmp_path / "raw")


def test_unsafe_member_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.tar"
    with tarfile.open(path, "w") as archive:
        info = tarfile.TarInfo("../escape.json")
        info.size = 2
        archive.addfile(info, io.BytesIO(b"{}"))
    with pytest.raises(ArchiveError):
        list(iter_json_documents(path))


def test_explicit_download_uses_stream_and_manifest(sample_archive: Path, tmp_path: Path) -> None:
    payload = sample_archive.read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.test/bench.tar.gz"
        return httpx.Response(200, content=payload, headers={"content-length": str(len(payload))})

    copied, manifest = download_official_archive(
        tmp_path / "raw",
        url="https://example.test/bench.tar.gz",
        max_bytes=len(payload) + 1,
        transport=httpx.MockTransport(handler),
    )
    assert copied.read_bytes() == payload
    assert manifest.source_uri == "https://example.test/bench.tar.gz"


def test_download_rejects_declared_size_over_limit(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=b"too large"))
    with pytest.raises(ArchiveError):
        download_official_archive(tmp_path, max_bytes=2, transport=transport)
    assert not (tmp_path / ".downloads" / "bench-release.tar.gz.part").exists()


def test_download_resumes_partial_archive(sample_archive: Path, tmp_path: Path) -> None:
    payload = sample_archive.read_bytes()
    cut = len(payload) // 2
    staging = tmp_path / ".downloads"
    staging.mkdir()
    (staging / "bench-release.tar.gz.part").write_bytes(payload[:cut])

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Range"] == f"bytes={cut}-"
        return httpx.Response(206, content=payload[cut:])

    copied, _ = download_official_archive(
        tmp_path,
        url="https://example.test/resume.tar.gz",
        transport=httpx.MockTransport(handler),
    )
    assert copied.read_bytes() == payload
