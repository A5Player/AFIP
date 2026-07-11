from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_validation_governance import MarketIntentValidationGovernanceRuntime


def _report(index: int, **overrides):
    payload = {
        "calibration_id": f"QCNF-{index:016X}", "status": "READY", "milestone": "Q", "pack": "7",
        "calibration_timestamp": 30000 + index * 1000,
        "total_validation_window_count": 9,
        "calibrated_confidence_score": 88.0,
        "evidence_coverage_score": 100.0,
        "calibration_accepted": True,
        "data_quality_certified": True, "future_safe": True,
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


def test_ready_governance_is_deterministic_and_complete():
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(_reports(), governance_timestamp=40000)
    assert result.status == "READY"
    assert result.governance_id.startswith("QGOV-")
    assert result.validation_governance_accepted is True
    assert result.review_required is False
    assert result.governance_band in {"STRONG", "ACCEPTABLE", "CAUTIOUS"}


def test_governance_report_is_immutable_and_deterministic():
    runtime = MarketIntentValidationGovernanceRuntime()
    first = runtime.evaluate_many(_reports(), governance_timestamp=40000)
    assert first == runtime.evaluate_many(_reports(), governance_timestamp=40000)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["pack"] = "6"
    rows[1]["calibration_id"] = rows[0]["calibration_id"]
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(rows, governance_timestamp=40000)
    assert "pack_7_lineage_invalid" in result.block_reasons
    assert "duplicate_or_invalid_pack_7_calibration_id" in result.block_reasons


def test_blocks_unaccepted_calibration_and_low_thresholds():
    rows = _reports()
    rows[1].update(status="BLOCKED", calibration_accepted=False, calibrated_confidence_score=40.0,
                   evidence_coverage_score=50.0)
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(rows, governance_timestamp=40000)
    assert "pack_7_calibration_not_accepted" in result.block_reasons
    assert "minimum_confidence_threshold_not_met" in result.block_reasons
    assert "minimum_evidence_coverage_threshold_not_met" in result.block_reasons
    assert result.review_required is True


def test_blocks_insufficient_reports_and_invalid_chronology():
    rows = [_report(2), _report(1)]
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(
        rows, governance_timestamp=20000, minimum_report_count=3,
    )
    assert "minimum_calibration_report_count_not_met" in result.block_reasons
    assert "market_intent_governance_chronology_invalid" in result.block_reasons


def test_blocks_invalid_metrics():
    rows = _reports()
    rows[0]["calibrated_confidence_score"] = float("nan")
    rows[1]["evidence_coverage_score"] = 101.0
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(rows, governance_timestamp=40000)
    assert "market_intent_governance_metrics_invalid" in result.block_reasons


def test_blocks_quality_future_prerequisite_and_policy_failures():
    rows = _reports()
    rows[0]["data_quality_certified"] = False
    rows[1]["future_safe"] = False
    rows[1]["market_regime_before_intent"] = False
    rows[2]["market_behaviour_before_intent"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(rows, governance_timestamp=40000)
    assert "data_quality_not_certified" in result.block_reasons
    assert "future_leakage_detected" in result.block_reasons
    assert "market_regime_not_evaluated_before_intent" in result.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_production_and_execution_authority_remain_disabled():
    result = MarketIntentValidationGovernanceRuntime().evaluate_many(_reports(), governance_timestamp=40000)
    assert result.research_only is True
    assert result.automatic_parameter_update_allowed is False
    assert result.trading_logic_change_allowed is False
    assert result.production_knowledge_allowed is False
    assert result.production_certification_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
