from dataclasses import FrozenInstanceError
import pytest

from afip.market_behaviour_confidence_calibration import MarketBehaviourConfidenceCalibrationRuntime


def _report(index: int, **overrides):
    row = {
        "report_id": f"PBDR-{index:016X}",
        "status": "READY",
        "schema_version": "AFIP_MARKET_BEHAVIOUR_DRIFT_DETECTION_V1",
        "detection_timestamp": 1000 * index,
        "baseline_transition_count": 81,
        "recent_transition_count": 81,
        "persistence_drift": -0.02,
        "regime_change_rate_drift": 0.02,
        "behaviour_change_rate_drift": 0.01,
        "stable_window_rate_drift": -0.04,
        "data_quality_certified": True,
        "future_safe": True,
        "market_regime_before_behaviour": True,
        "drift_detected": False,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    row.update(overrides)
    return row


def _reports():
    return [_report(i) for i in range(1, 4)]


def test_ready_calibration_produces_deterministic_confidence():
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(_reports(), calibration_timestamp=4000)
    assert result.status == "READY"
    assert result.calibration_id.startswith("PBCF-")
    assert result.report_count == 3
    assert result.total_transition_count == 486
    assert result.calibrated_confidence_score >= 60.0
    assert result.confidence_band in {"HIGH", "MODERATE", "CAUTIOUS"}


def test_calibration_is_deterministic_and_immutable():
    runtime = MarketBehaviourConfidenceCalibrationRuntime()
    first = runtime.evaluate_many(_reports(), calibration_timestamp=4000)
    second = runtime.evaluate_many(_reports(), calibration_timestamp=4000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_pack_6_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["schema_version"] = "OTHER"
    rows[1]["report_id"] = rows[0]["report_id"]
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(rows, calibration_timestamp=4000)
    assert "pack_6_drift_not_accepted" in result.block_reasons
    assert "duplicate_or_invalid_drift_report_id" in result.block_reasons


def test_blocks_insufficient_coverage_and_invalid_chronology():
    rows = [_report(2), _report(1)]
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(
        rows, calibration_timestamp=1500, minimum_report_count=3, minimum_total_transition_count=1000
    )
    assert "minimum_report_count_not_met" in result.block_reasons
    assert "minimum_transition_count_not_met" in result.block_reasons
    assert "market_behaviour_confidence_chronology_invalid" in result.block_reasons


def test_blocks_future_leakage_and_uncertified_data():
    rows = _reports()
    rows[0]["future_safe"] = False
    rows[1]["data_quality_certified"] = False
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(rows, calibration_timestamp=4000)
    assert "future_leakage_detected" in result.block_reasons
    assert "data_quality_not_certified" in result.block_reasons


def test_blocks_low_confidence_from_excessive_drift():
    rows = _reports()
    for row in rows:
        row["persistence_drift"] = 0.19
        row["regime_change_rate_drift"] = 0.24
        row["behaviour_change_rate_drift"] = 0.24
        row["stable_window_rate_drift"] = 0.34
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(
        rows, calibration_timestamp=4000, minimum_calibrated_confidence=70.0
    )
    assert "minimum_calibrated_confidence_not_met" in result.block_reasons
    assert not result.calibration_accepted


def test_blocks_non_finite_metric_regime_order_and_policy_violation():
    rows = _reports()
    rows[0]["persistence_drift"] = float("nan")
    rows[1]["market_regime_before_behaviour"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(rows, calibration_timestamp=4000)
    assert "non_finite_behaviour_confidence_metric" in result.block_reasons
    assert "market_regime_not_evaluated_before_behaviour" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    result = MarketBehaviourConfidenceCalibrationRuntime().evaluate_many(_reports(), calibration_timestamp=4000)
    assert result.research_only
    assert not result.automatic_parameter_update_allowed
    assert not result.trading_logic_change_allowed
    assert not result.production_knowledge_allowed
    assert not result.production_certification_granted
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert not result.direct_execution
    assert not result.live_execution_enabled
    assert result.order_status == "NO_ORDER_SENT"
    assert not result.broker_request_created
    assert not result.order_transmission_attempted
    assert not result.position_modification_attempted
