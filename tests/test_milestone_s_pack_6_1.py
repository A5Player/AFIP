from dataclasses import replace
import json

import pytest

from afip.knowledge_validation.runtime import (
    KnowledgeValidationEngine, ValidationEvidence,
    evidence_from_evolution_report, write_validation_report,
)


def ev(i, period, regime, exp=10, ci=2, stability=85, confidence=88, status="RESEARCH_CERTIFIED", samples=100):
    return ValidationEvidence(str(i), "candidate-a", "pattern=alpha", period, regime, samples,
                              exp, ci, stability, confidence, "report-"+str(i), status)


def test_policy_has_no_execution_authority():
    policy=json.load(open("config/knowledge_validation/validation_policy.json", encoding="utf-8"))
    assert policy["execution_authority"] == "NONE"
    assert policy["promotion_to_execution"] == "PROHIBITED"
    assert policy["automatic_trading_policy_change"] == "PROHIBITED"


def test_strong_cross_period_evidence_is_research_review_ready():
    report=KnowledgeValidationEngine().validate([ev(1,"p1","TREND"),ev(2,"p2","RANGE"),ev(3,"p3","TREND")])
    d=report.decisions[0]
    assert d.validation_status == "VALIDATED_FOR_RESEARCH_REVIEW"
    assert d.research_promotion_status == "RESEARCH_REVIEW_READY"
    assert d.execution_authority == "NONE"
    assert d.human_approval_required is True


def test_insufficient_periods_remain_pending():
    d=KnowledgeValidationEngine().validate([ev(1,"p1","TREND"),ev(2,"p2","RANGE")]).decisions[0]
    assert d.validation_status == "VALIDATION_PENDING"
    assert "MINIMUM_INDEPENDENT_PERIODS_NOT_MET" in d.reasons


def test_insufficient_regimes_remain_pending():
    d=KnowledgeValidationEngine().validate([ev(1,"p1","TREND"),ev(2,"p2","TREND"),ev(3,"p3","TREND")]).decisions[0]
    assert "MINIMUM_MARKET_REGIMES_NOT_MET" in d.reasons


def test_rejected_source_rejects_decision():
    d=KnowledgeValidationEngine().validate([ev(1,"p1","TREND"),ev(2,"p2","RANGE"),ev(3,"p3","TREND",status="REJECTED")]).decisions[0]
    assert d.validation_status == "REJECTED"


def test_zero_positive_ci_rejects_decision():
    d=KnowledgeValidationEngine().validate([ev(1,"p1","TREND",ci=-1),ev(2,"p2","RANGE",ci=-1),ev(3,"p3","TREND",ci=-1)]).decisions[0]
    assert d.validation_status == "REJECTED"


def test_duplicate_evidence_is_deduplicated():
    item=ev(1,"p1","TREND")
    report=KnowledgeValidationEngine().validate([item,item])
    assert report.evidence_count == 1


def test_report_is_deterministic(tmp_path):
    items=[ev(1,"p1","TREND"),ev(2,"p2","RANGE"),ev(3,"p3","TREND")]
    engine=KnowledgeValidationEngine()
    a=engine.validate(items); b=engine.validate(list(reversed(items)))
    assert a.report_id == b.report_id
    assert write_validation_report(a,tmp_path/"a.json") == write_validation_report(b,tmp_path/"b.json")


def test_evolution_conversion_rejects_authority():
    with pytest.raises(ValueError):
        evidence_from_evolution_report({"report_id":"r","execution_authority":"ORDER","promotion_to_execution":"PROHIBITED","candidates":[]},"p","TREND")


def test_evolution_conversion():
    source={"report_id":"r","execution_authority":"NONE","promotion_to_execution":"PROHIBITED","candidates":[{
        "candidate_id":"c","hypothesis_key":"h","total_samples":150,"weighted_expectancy_points":4,
        "latest_confidence_interval_low":1,"latest_stability_score":80,"knowledge_confidence_score":82,
        "lifecycle_status":"RESEARCH_CERTIFIED"}]}
    result=evidence_from_evolution_report(source,"2026-Q1","TREND")
    assert len(result)==1 and result[0].candidate_id=="c"


def test_candidate_hypothesis_mismatch_rejected():
    with pytest.raises(ValueError):
        KnowledgeValidationEngine().validate([ev(1,"p1","TREND"),replace(ev(2,"p2","RANGE"),hypothesis_key="other")])


def test_invalid_ratio_threshold_rejected():
    with pytest.raises(ValueError):
        KnowledgeValidationEngine(minimum_positive_ci_ratio=1.1)


def test_module_contains_no_broker_or_order_calls():
    import inspect
    import afip.knowledge_validation.runtime as runtime
    source=inspect.getsource(runtime).lower()
    for forbidden in ("order_send(", "mt5.initialize(", "broker.login(", "position_size("):
        assert forbidden not in source
