import pandas as pd
import pytest

from adaptiveai.registry import (
    exact_model_mapping,
    usd_per_token_to_per_million,
    write_mapping_report,
)
from adaptiveai.schemas import OpenRouterModel


def test_cost_unit_conversion() -> None:
    assert usd_per_token_to_per_million("0.000003") == pytest.approx(3.0)
    assert usd_per_token_to_per_million(None) is None
    assert usd_per_token_to_per_million("-1") is None


def test_model_mapping_is_exact_only() -> None:
    catalog = pd.DataFrame({"model_id": ["org/model-v2"], "canonical_slug": ["org/model-v2"]})
    assert exact_model_mapping("org/model-v2", catalog) == "org/model-v2"
    assert exact_model_mapping("model v2", catalog) is None


def test_catalog_schema_preserves_structured_pricing_overrides() -> None:
    model = OpenRouterModel.model_validate(
        {
            "id": "org/model",
            "pricing": {
                "prompt": "0.000001",
                "overrides": [{"min_prompt_tokens": 1000, "prompt": "0.0000005"}],
            },
        }
    )
    assert isinstance(model.pricing["overrides"], list)


def test_mapping_report_leaves_approximate_names_unresolved(tmp_path) -> None:
    benchmark = pd.DataFrame({"source_model_id": ["model v2", "org/model-v2"]})
    catalog = pd.DataFrame({"model_id": ["org/model-v2"], "canonical_slug": ["org/model-v2"]})
    report = write_mapping_report(benchmark, catalog, tmp_path / "mapping.parquet")
    assert (
        report.set_index("llmrouterbench_model_id").loc["model v2", "mapping_status"]
        == "unresolved"
    )
    assert (
        report.set_index("llmrouterbench_model_id").loc["org/model-v2", "mapping_status"] == "exact"
    )
