from dataclasses import FrozenInstanceError
import pytest

from afip.market_behaviour_drift_detection import MarketBehaviourDriftDetectionRuntime


def _report(index: int, **overrides):
    recent = index > 3
    row = {
        "report_id": f"PBST-{index:016X}",
        "status": "READY",
        "schema_version": "AFIP_MARKET_BEHAVIOUR_STABILITY_VALIDATION_V1",
        "validation_timestamp": 1000 * index,
        "total_transition_count": 27,
        "mean_persistence_ratio": 0.70 if not recent else 0.68,
        "mean_regime_change_rate": 0.20 if not recent else 0.22,
        "mean_behaviour_change_rate": 0.24 if not recent else 0.25,
        "stable_window_rate": 0.80 if not recent else 0.76,
        "data_quality_certified": True,
        "future_safe": True,
        "market_regime_before_behaviour": True,
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    row.update(overrides)
    return row


def _reports():
    return [_report(i) for i in range(1, 7)]


def test_ready_drift_report_compares_baseline_and_recent_segments():
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(_reports(), detection_timestamp=7000)
    assert result.status == "READY"
    assert result.schema_version == "AFIP_MARKET_BEHAVIOUR_DRIFT_DETECTION_V1"
    assert result.baseline_window_count == 3
    assert result.recent_window_count == 3
    assert result.baseline_transition_count == 81
    assert result.recent_transition_count == 81
    assert result.persistence_drift == pytest.approx(-0.02)
    assert not result.drift_detected
    assert result.report_id.startswith("PBDR-")


def test_drift_report_is_deterministic_and_immutable():
    runtime = MarketBehaviourDriftDetectionRuntime()
    first = runtime.evaluate_many(_reports(), detection_timestamp=7000)
    second = runtime.evaluate_many(_reports(), detection_timestamp=7000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_pack_5_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["schema_version"] = "OTHER"
    rows[1]["report_id"] = rows[0]["report_id"]
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(rows, detection_timestamp=7000)
    assert "pack_5_stability_lineage_invalid" in result.block_reasons
    assert "duplicate_stability_report_id_detected" in result.block_reasons


def test_blocks_insufficient_segment_coverage_and_invalid_chronology():
    rows = [_report(2), _report(1), _report(3)]
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(
        rows, detection_timestamp=2500, minimum_transitions_per_segment=100
    )
    assert "insufficient_drift_window_count" in result.block_reasons
    assert "baseline_transition_coverage_not_met" in result.block_reasons
    assert "recent_transition_coverage_not_met" in result.block_reasons
    assert "market_behaviour_drift_chronology_invalid" in result.block_reasons


def test_blocks_future_leakage_and_uncertified_data():
    rows = _reports()
    rows[0]["future_safe"] = False
    rows[1]["data_quality_certified"] = False
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(rows, detection_timestamp=7000)
    assert "future_leakage_detected" in result.block_reasons
    assert "data_quality_not_certified" in result.block_reasons


def test_blocks_excessive_persistence_and_change_rate_drift():
    rows = _reports()
    for row in rows[3:]:
        row["mean_persistence_ratio"] = 0.30
        row["mean_regime_change_rate"] = 0.70
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(rows, detection_timestamp=7000)
    assert "persistence_drift_limit_exceeded" in result.block_reasons
    assert "change_rate_drift_limit_exceeded" in result.block_reasons
    assert result.drift_detected


def test_blocks_invalid_metrics_regime_order_and_policy_violation():
    rows = _reports()
    rows[0]["stable_window_rate"] = float("nan")
    rows[1]["market_regime_before_behaviour"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(rows, detection_timestamp=7000)
    assert "market_behaviour_drift_metrics_invalid" in result.block_reasons
    assert "market_regime_not_evaluated_before_behaviour" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    result = MarketBehaviourDriftDetectionRuntime().evaluate_many(_reports(), detection_timestamp=7000)
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
