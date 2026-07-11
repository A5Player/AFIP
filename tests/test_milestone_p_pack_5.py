from dataclasses import FrozenInstanceError
import pytest

from afip.market_behaviour_stability_validation import MarketBehaviourStabilityValidationRuntime


def _report(index: int, **overrides):
    row = {
        "report_id": f"PBTS-{index:016X}",
        "status": "READY",
        "schema_version": "AFIP_MARKET_BEHAVIOUR_TRANSITION_STATISTICS_V1",
        "statistics_timestamp": 1000 * index,
        "sequence_report_count": 3,
        "total_transition_count": 9,
        "weighted_persistence_ratio": 0.70 + (index - 2) * 0.02,
        "regime_change_rate": 0.20 + (index - 2) * 0.02,
        "behaviour_change_rate": 0.22 + (index - 2) * 0.02,
        "dominant_market_regime": "TREND",
        "dominant_behaviour_state": "DIRECTIONAL_PERSISTENCE",
        "data_quality_certified": True,
        "future_safe": True,
        "market_regime_before_behaviour": True,
        "broker": "XM",
        "symbol": "GOLD#",
        "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT",
        "direct_execution": False,
        "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False,
        "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    row.update(overrides)
    return row


def _reports():
    return [_report(1), _report(2), _report(3)]


def test_ready_stability_report_contains_cross_window_metrics():
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(_reports(), validation_timestamp=4000)
    assert result.status == "READY"
    assert result.schema_version == "AFIP_MARKET_BEHAVIOUR_STABILITY_VALIDATION_V1"
    assert result.window_count == 3
    assert result.total_transition_count == 27
    assert result.mean_persistence_ratio == pytest.approx(0.70)
    assert result.dominant_regime_consistency_rate == 1.0
    assert result.stable_window_rate == 1.0
    assert result.report_id.startswith("PBST-")


def test_stability_report_is_deterministic_and_immutable():
    runtime = MarketBehaviourStabilityValidationRuntime()
    first = runtime.evaluate_many(_reports(), validation_timestamp=4000)
    second = runtime.evaluate_many(_reports(), validation_timestamp=4000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_pack_4_lineage_and_duplicate_ids():
    rows = _reports()
    rows[0]["schema_version"] = "OTHER"
    rows[1]["report_id"] = rows[0]["report_id"]
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(rows, validation_timestamp=4000)
    assert "pack_4_transition_statistics_lineage_invalid" in result.block_reasons
    assert "duplicate_transition_statistics_report_id_detected" in result.block_reasons


def test_blocks_insufficient_coverage_and_invalid_chronology():
    rows = [_report(2), _report(1)]
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(rows, validation_timestamp=1500)
    assert "insufficient_stability_window_coverage" in result.block_reasons
    assert "market_behaviour_stability_chronology_invalid" in result.block_reasons


def test_blocks_future_leakage_and_uncertified_data():
    rows = _reports()
    rows[0]["future_safe"] = False
    rows[1]["data_quality_certified"] = False
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(rows, validation_timestamp=4000)
    assert "future_leakage_detected" in result.block_reasons
    assert "data_quality_not_certified" in result.block_reasons


def test_blocks_excessive_variability_and_low_consistency():
    rows = _reports()
    rows[0]["weighted_persistence_ratio"] = 0.10
    rows[1]["weighted_persistence_ratio"] = 0.90
    rows[0]["regime_change_rate"] = 0.00
    rows[1]["regime_change_rate"] = 0.90
    rows[1]["dominant_market_regime"] = "RANGE"
    rows[2]["dominant_market_regime"] = "TRANSITION"
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(rows, validation_timestamp=4000)
    assert "persistence_variability_exceeds_limit" in result.block_reasons
    assert "change_rate_variability_exceeds_limit" in result.block_reasons
    assert "dominant_state_consistency_below_minimum" in result.block_reasons


def test_blocks_invalid_metrics_regime_order_and_policy_violation():
    rows = _reports()
    rows[0]["weighted_persistence_ratio"] = float("nan")
    rows[1]["market_regime_before_behaviour"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(rows, validation_timestamp=4000)
    assert "transition_statistics_metrics_invalid" in result.block_reasons
    assert "market_regime_not_evaluated_before_behaviour" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    result = MarketBehaviourStabilityValidationRuntime().evaluate_many(_reports(), validation_timestamp=4000)
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
