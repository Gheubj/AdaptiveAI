import json

from adaptiveai.phase45_benchmark import (
    benchmark_v2,
    score_response,
    scorer_validation_cases,
)


def test_benchmark_v2_is_frozen_unique_and_stratified():
    panel = benchmark_v2()
    assert panel.groupby("split").size().to_dict() == {
        "test": 250,
        "train": 150,
        "validation": 100,
    }
    assert panel.prompt.nunique() == 500
    assert set(panel.task) == {
        "math",
        "factual",
        "extraction",
        "instruction",
        "programming",
        "reasoning",
    }
    assert not panel.prompt.str.contains("Return only the capital of Canada.", regex=False).any()


def test_scorer_validation_suite_has_no_errors():
    cases = scorer_validation_cases()
    assert len(cases) >= 12
    assert (cases.expected == cases.observed).all()


def test_numeric_scorer_rejects_ambiguous_containment():
    assert score_response("Answer: 7.000000", "7", "number").correct
    result = score_response("It could be 6 or 7", "7", "number")
    assert not result.correct
    assert result.status == "unscorable"


def test_json_scorer_validates_exact_schema_and_fields():
    reference = json.dumps({"order": "ZX-100", "amount": 10})
    assert score_response('{"amount": 10, "order": "ZX-100"}', reference, "json").correct
    assert not score_response('{"order": "ZX-100"}', reference, "json").correct
    assert not score_response(
        '{"order": "ZX-100", "amount": 10, "extra": 1}', reference, "json"
    ).correct
