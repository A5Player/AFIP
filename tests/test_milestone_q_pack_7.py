from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_confidence_calibration import MarketIntentConfidenceCalibrationRuntime


def _report(index: int, **overrides):
    payload = {
        "drift_id": f"QDRF-{index:016X}", "status": "READY", "milestone": "Q", "pack": "6",
        "detection_start_timestamp": 20000 + index * 3000,
        "detection_end_timestamp": 21000 + index * 3000,
        "validation_window_count": 3,
        "persistence_mean_delta": 0.02,
        "intensity_mean_delta": 0.02,
        "stability_score_delta": -0.01,
        "stable_window_ratio_delta": 0.0,
        "pattern_consistency_delta": 0.0,
        "drift_score": 0.04,
        "drift_band": "LOW", "drift_detected": False, "review_required": False,
        "data_quality_certified": True, "future_safe": True,
        "market_regime_before_intent": True, "market_behaviour_before_intent": True,
        "policy_version": "AFIP_V1_FEATURE_FREEZE", "broker": "XM", "symbol": "GOLD#",
        "base_lot_per_unit": 0.01, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    payload.update(overrides)
    return payload


def _reports():
    return [_report(1), _report(2), _report(3)]


def test_ready_calibration_produces_deterministic_confidence():
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(_reports(), calibration_timestamp=31000)
    assert result.status == "READY"
    assert result.calibration_id.startswith("QCNF-")
    assert result.report_count == 3
    assert result.total_validation_window_count == 9
    assert result.calibrated_confidence_score >= 60.0
    assert result.confidence_band in {"HIGH", "MODERATE", "CAUTIOUS"}


def test_calibration_is_deterministic_and_immutable():
    runtime = MarketIntentConfidenceCalibrationRuntime()
    first = runtime.evaluate_many(_reports(), calibration_timestamp=31000)
    assert first == runtime.evaluate_many(_reports(), calibration_timestamp=31000)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_pack_6_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["pack"] = "5"
    rows[1]["drift_id"] = rows[0]["drift_id"]
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(rows, calibration_timestamp=31000)
    assert "pack_6_drift_not_accepted" in result.block_reasons
    assert "duplicate_or_invalid_pack_6_drift_id" in result.block_reasons


def test_blocks_detected_drift_and_review_requirement():
    rows = _reports()
    rows[1].update(drift_detected=True, review_required=True, drift_band="MODERATE")
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(rows, calibration_timestamp=31000)
    assert "pack_6_drift_not_accepted" in result.block_reasons
    assert result.calibration_accepted is False


def test_blocks_insufficient_coverage_and_invalid_chronology():
    rows = [_report(2), _report(1)]
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(
        rows, calibration_timestamp=20000, minimum_report_count=3,
        minimum_total_validation_window_count=20,
    )
    assert "minimum_report_count_not_met" in result.block_reasons
    assert "minimum_validation_window_count_not_met" in result.block_reasons
    assert "market_intent_confidence_chronology_invalid" in result.block_reasons


def test_blocks_invalid_metrics_and_low_confidence():
    rows = _reports()
    for row in rows:
        row.update(drift_score=0.34, persistence_mean_delta=0.34, intensity_mean_delta=0.34,
                   stability_score_delta=0.34, stable_window_ratio_delta=0.34,
                   pattern_consistency_delta=0.34)
    rows[0]["drift_score"] = float("nan")
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(
        rows, calibration_timestamp=31000, minimum_calibrated_confidence=70.0,
    )
    assert "market_intent_confidence_metrics_invalid" in result.block_reasons
    assert "minimum_calibrated_confidence_not_met" in result.block_reasons


def test_blocks_quality_future_prerequisite_and_policy_failures():
    rows = _reports()
    rows[0]["data_quality_certified"] = False
    rows[1]["future_safe"] = False
    rows[1]["market_regime_before_intent"] = False
    rows[2]["market_behaviour_before_intent"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(rows, calibration_timestamp=31000)
    assert "data_quality_not_certified" in result.block_reasons
    assert "future_leakage_detected" in result.block_reasons
    assert "market_regime_not_evaluated_before_intent" in result.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    result = MarketIntentConfidenceCalibrationRuntime().evaluate_many(_reports(), calibration_timestamp=31000)
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
