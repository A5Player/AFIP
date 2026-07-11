from dataclasses import FrozenInstanceError
import pytest

from afip.market_behaviour_transition_statistics import MarketBehaviourTransitionStatisticsRuntime


def _report(index: int, **overrides):
    item = {
        "report_id": f"PBSQ-{index:016X}",
        "status": "READY",
        "schema_version": "AFIP_MARKET_BEHAVIOUR_SEQUENCE_V1",
        "sequence_start_timestamp": 1000 + index * 1000,
        "sequence_end_timestamp": 1400 + index * 1000,
        "state_count": 4,
        "transition_count": 3,
        "regime_change_count": 1,
        "behaviour_change_count": 1,
        "direction_change_count": 1,
        "persistence_ratio": 2 / 3,
        "dominant_market_regime": "TREND",
        "dominant_behaviour_state": "DIRECTIONAL_PERSISTENCE",
        "transition_signature": (
            "TREND:DIRECTIONAL_PERSISTENCE:BUY->TREND:DIRECTIONAL_PERSISTENCE:BUY",
            "TREND:DIRECTIONAL_PERSISTENCE:BUY->TREND:DIRECTIONAL_PERSISTENCE:BUY",
            "TREND:DIRECTIONAL_PERSISTENCE:BUY->TRANSITION:REGIME_TRANSITION:FLAT",
        ),
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
    item.update(overrides)
    return item


def _reports():
    return [_report(1), _report(2), _report(3)]


def test_ready_transition_statistics_contain_aggregated_metrics():
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(_reports(), statistics_timestamp=5000)
    assert result.status == "READY"
    assert result.schema_version == "AFIP_MARKET_BEHAVIOUR_TRANSITION_STATISTICS_V1"
    assert result.sequence_report_count == 3
    assert result.total_state_count == 12
    assert result.total_transition_count == 9
    assert result.total_regime_change_count == 3
    assert result.weighted_persistence_ratio == pytest.approx(2 / 3, abs=1e-6)
    assert result.report_id.startswith("PBTS-")


def test_transition_statistics_are_deterministic_and_immutable():
    runtime = MarketBehaviourTransitionStatisticsRuntime()
    first = runtime.evaluate_many(_reports(), statistics_timestamp=5000)
    second = runtime.evaluate_many(_reports(), statistics_timestamp=5000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_pack_3_lineage_and_duplicate_report_ids():
    rows = _reports()
    rows[0]["schema_version"] = "OTHER"
    rows[1]["report_id"] = rows[0]["report_id"]
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(rows, statistics_timestamp=5000)
    assert "pack_3_sequence_lineage_invalid" in result.block_reasons
    assert "duplicate_sequence_report_id_detected" in result.block_reasons


def test_blocks_insufficient_coverage_and_invalid_chronology():
    rows = [_report(2), _report(1)]
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(rows, statistics_timestamp=2500)
    assert "insufficient_sequence_report_coverage" in result.block_reasons
    assert "transition_statistics_chronology_invalid" in result.block_reasons


def test_blocks_future_leakage_and_uncertified_data():
    rows = _reports()
    rows[0]["future_safe"] = False
    rows[1]["data_quality_certified"] = False
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(rows, statistics_timestamp=5000)
    assert "future_leakage_detected" in result.block_reasons
    assert "data_quality_not_certified" in result.block_reasons


def test_transition_frequency_order_is_deterministic():
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(_reports(), statistics_timestamp=5000)
    assert result.most_common_transition == "TREND:DIRECTIONAL_PERSISTENCE:BUY->TREND:DIRECTIONAL_PERSISTENCE:BUY"
    assert result.transition_frequencies[0][1] == 6
    assert result.dominant_market_regime == "TREND"
    assert result.dominant_behaviour_state == "DIRECTIONAL_PERSISTENCE"


def test_blocks_invalid_metrics_regime_order_and_policy_violation():
    rows = _reports()
    rows[0]["transition_count"] = 99
    rows[1]["market_regime_before_behaviour"] = False
    rows[2]["broker"] = "OTHER"
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(rows, statistics_timestamp=5000)
    assert "sequence_metrics_invalid" in result.block_reasons
    assert "market_regime_not_evaluated_before_behaviour" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    result = MarketBehaviourTransitionStatisticsRuntime().evaluate_many(_reports(), statistics_timestamp=5000)
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
