from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_review_certification import MarketIntentReviewCertificationRuntime


def _report(index: int, **overrides):
    payload = {
        "governance_id": f"QGOV-{index:016X}", "status": "READY", "milestone": "Q", "pack": "8",
        "governance_timestamp": 40000 + index * 1000,
        "calibration_report_count": 3, "total_validation_window_count": 27,
        "governance_score": 92.0, "validation_governance_accepted": True,
        "review_required": False, "data_quality_certified": True, "future_safe": True,
        "market_regime_before_intent": True, "market_behaviour_before_intent": True,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False, "production_certification_granted": False,
    }
    payload.update(overrides)
    return payload


def _reports():
    return [_report(1), _report(2), _report(3)]


def test_ready_review_certification_is_deterministic_and_complete():
    result = MarketIntentReviewCertificationRuntime().certify_many(_reports(), certification_timestamp=50000)
    assert result.status == "READY"
    assert result.review_certification_id.startswith("QREV-")
    assert result.market_intent_review_certified is True
    assert result.milestone_q_completion_candidate is True
    assert result.review_required is False


def test_review_report_is_immutable_and_deterministic():
    runtime = MarketIntentReviewCertificationRuntime()
    first = runtime.certify_many(_reports(), certification_timestamp=50000)
    assert first == runtime.certify_many(_reports(), certification_timestamp=50000)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["pack"] = "7"
    rows[1]["governance_id"] = rows[0]["governance_id"]
    result = MarketIntentReviewCertificationRuntime().certify_many(rows, certification_timestamp=50000)
    assert "pack_8_lineage_invalid" in result.block_reasons
    assert "duplicate_or_invalid_pack_8_governance_id" in result.block_reasons


def test_blocks_unaccepted_or_pending_governance():
    rows = _reports()
    rows[1].update(status="BLOCKED", validation_governance_accepted=False, review_required=True)
    result = MarketIntentReviewCertificationRuntime().certify_many(rows, certification_timestamp=50000)
    assert "pack_8_governance_not_accepted" in result.block_reasons
    assert "pack_8_governance_review_pending" in result.block_reasons


def test_blocks_insufficient_reports_low_score_and_invalid_chronology():
    rows = [_report(2, governance_score=60.0), _report(1)]
    result = MarketIntentReviewCertificationRuntime().certify_many(
        rows, certification_timestamp=20000, minimum_report_count=3, minimum_governance_score=75.0,
    )
    assert "minimum_governance_report_count_not_met" in result.block_reasons
    assert "minimum_governance_score_not_met" in result.block_reasons
    assert "market_intent_review_chronology_invalid" in result.block_reasons


def test_blocks_invalid_metrics():
    rows = _reports()
    rows[0]["governance_score"] = float("nan")
    result = MarketIntentReviewCertificationRuntime().certify_many(rows, certification_timestamp=50000)
    assert "market_intent_review_metrics_invalid" in result.block_reasons


def test_blocks_quality_future_prerequisite_and_policy_failures():
    rows = _reports()
    rows[0]["data_quality_certified"] = False
    rows[1]["future_safe"] = False
    rows[1]["market_regime_before_intent"] = False
    rows[2]["market_behaviour_before_intent"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketIntentReviewCertificationRuntime().certify_many(rows, certification_timestamp=50000)
    assert "data_quality_not_certified" in result.block_reasons
    assert "future_leakage_detected" in result.block_reasons
    assert "market_regime_not_evaluated_before_intent" in result.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_production_release_and_execution_authority_remain_disabled():
    result = MarketIntentReviewCertificationRuntime().certify_many(_reports(), certification_timestamp=50000)
    assert result.research_only is True
    assert result.automatic_parameter_update_allowed is False
    assert result.trading_logic_change_allowed is False
    assert result.production_knowledge_allowed is False
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
