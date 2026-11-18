import os
from pathlib import Path

import pytest

from adaptiveai.io import iter_json_documents
from adaptiveai.normalize import infer_path_metadata
from adaptiveai.schemas import BenchmarkRecord


@pytest.mark.real_data
def test_first_real_archive_document_matches_import_contract() -> None:
    configured = os.getenv("ADAPTIVEAI_REAL_ARCHIVE")
    if not configured:
        pytest.skip("set ADAPTIVEAI_REAL_ARCHIVE to run the non-redistributed real-data check")
    archive = Path(configured)
    member, document = next(iter_json_documents(archive))
    dataset, _, model = infer_path_metadata(member)
    assert dataset == document["dataset_name"]
    assert model == document["model_name"]
    assert document["counts"] == len(document["records"])
    BenchmarkRecord.model_validate(document["records"][0])
