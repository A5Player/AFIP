from pathlib import Path
import json
import pytest

from afip.data_quality import DataQualityScorer, QualityDimensions


def dims(value=100):
    return QualityDimensions(
        completeness=value,
        consistency=value,
        validity=value,
        freshness=value,
        lineage=value,
        documentation=value,
        integrity=value,
    )


def test_policy_has_no_execution_authority():
    assert DataQualityScorer().policy.get("execution_authority", "NONE") == "NONE"


def test_rejects_execution_authority():
    with pytest.raises(ValueError):
        DataQualityScorer({"execution_authority": "LIVE"})


def test_certified_high_quality_is_research_ready():
    result = DataQualityScorer().assess("d1", dims(95), certification_status="CERTIFIED")
    assert result.readiness_level == "RESEARCH_READY"
    assert result.usage_restriction == "APPROVED_RESEARCH_ONLY"


def test_uncertified_high_quality_not_fully_ready():
    result = DataQualityScorer().assess("d1", dims(95), certification_status="UNCERTIFIED")
    assert result.readiness_level == "CONDITIONALLY_READY"


def test_corrupted_caps_score():
    result = DataQualityScorer().assess("d1", dims(100), integrity_status="CORRUPTED")
    assert result.overall_score <= 39.99
    assert result.usage_restriction == "RECOVERY_ONLY"


def test_quarantined_is_prohibited():
    result = DataQualityScorer().assess("d1", dims(100), integrity_status="QUARANTINED")
    assert result.usage_restriction == "PROHIBITED"


def test_unregistered_dataset_is_capped():
    result = DataQualityScorer().assess("d1", dims(100), catalog_registered=False)
    assert result.overall_score <= 59.99


def test_low_dimension_reason_is_recorded():
    result = DataQualityScorer().assess("d1", QualityDimensions(20,100,100,100,100,100,100))
    assert "low_completeness" in result.reasons


def test_values_are_clamped():
    result = DataQualityScorer().assess("d1", QualityDimensions(120,-5,100,100,100,100,100))
    assert result.dimensions.completeness == 100.0
    assert result.dimensions.consistency == 0.0


def test_weights_must_sum_to_one():
    scorer = DataQualityScorer({"weights": {
        "completeness": 1,
        "consistency": 1,
        "validity": 1,
        "freshness": 1,
        "lineage": 1,
        "documentation": 1,
        "integrity": 1,
    }})
    with pytest.raises(ValueError):
        scorer.assess("d1", dims())


def test_assessment_id_is_deterministic():
    scorer = DataQualityScorer()
    a = scorer.assess("d1", dims(80))
    b = scorer.assess("d1", dims(80))
    assert a.assessment_id == b.assessment_id


def test_append_only_ledger(tmp_path):
    scorer = DataQualityScorer()
    result = scorer.assess("d1", dims(80))
    ledger = tmp_path / "quality.jsonl"
    scorer.append_assessment_ledger(result, ledger)
    scorer.append_assessment_ledger(result, ledger)
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2


def test_module_contains_no_broker_or_order_calls():
    source = Path("afip/data_quality/runtime.py").read_text(encoding="utf-8").lower()
    forbidden = ("metatrader5", "order_send(", "order_check(", "mt5.", "broker.login")
    assert not any(token in source for token in forbidden)
