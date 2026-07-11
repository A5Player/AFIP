from dataclasses import FrozenInstanceError
import pytest

from afip.market_behaviour_intelligence_foundation import MarketBehaviourIntelligenceFoundationRuntime


def _payload(**overrides):
    payload = {
        "observed_timestamp": 2000,
        "source_timestamp": 1900,
        "market_regime": "TREND",
        "market_regime_evaluated_first": True,
        "direction": "BUY",
        "trend_efficiency": 0.82,
        "volatility_ratio": 1.25,
        "range_position": 0.78,
        "momentum_persistence": 0.72,
        "liquidity_condition": "NORMAL",
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "policy_version": "AFIP_V1_FEATURE_FREEZE",
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
    payload.update(overrides)
    return payload


def test_ready_observation_classifies_directional_persistence():
    report = MarketBehaviourIntelligenceFoundationRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.behaviour_state == "DIRECTIONAL_PERSISTENCE"
    assert report.observation_id.startswith("PBEH-")


def test_observation_is_deterministic_and_immutable():
    runtime = MarketBehaviourIntelligenceFoundationRuntime()
    first = runtime.evaluate_one(_payload())
    second = runtime.evaluate_one(_payload())
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_future_leakage_and_invalid_chronology():
    report = MarketBehaviourIntelligenceFoundationRuntime().evaluate_one(
        _payload(future_leakage_detected=True, observed_timestamp=1800)
    )
    assert "future_leakage_detected" in report.block_reasons
    assert "behaviour_observation_chronology_invalid" in report.block_reasons


def test_blocks_when_market_regime_not_evaluated_first():
    report = MarketBehaviourIntelligenceFoundationRuntime().evaluate_one(
        _payload(market_regime_evaluated_first=False)
    )
    assert "market_regime_not_evaluated_before_behaviour" in report.block_reasons


def test_blocks_invalid_metrics_and_non_finite_values():
    report = MarketBehaviourIntelligenceFoundationRuntime().evaluate_one(
        _payload(trend_efficiency=1.5, volatility_ratio=float("inf"))
    )
    assert "behaviour_metrics_invalid" in report.block_reasons


def test_classifies_range_and_volatility_behaviour_deterministically():
    runtime = MarketBehaviourIntelligenceFoundationRuntime()
    range_report = runtime.evaluate_one(_payload(market_regime="RANGE", direction="FLAT", trend_efficiency=0.2, momentum_persistence=0.1))
    shock_report = runtime.evaluate_one(_payload(volatility_ratio=2.5))
    assert range_report.behaviour_state == "RANGE_ROTATION"
    assert shock_report.behaviour_state == "VOLATILITY_EXPANSION"


def test_blocks_data_quality_and_policy_violation():
    report = MarketBehaviourIntelligenceFoundationRuntime().evaluate_one(
        _payload(data_quality_certified=False, broker="OTHER")
    )
    assert "data_quality_not_certified" in report.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in report.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    report = MarketBehaviourIntelligenceFoundationRuntime().evaluate_one(_payload())
    assert report.research_only is True
    assert report.automatic_parameter_update_allowed is False
    assert report.trading_logic_change_allowed is False
    assert report.production_knowledge_allowed is False
    assert report.production_certification_granted is False
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.order_status == "NO_ORDER_SENT"
    assert report.broker_request_created is False
    assert report.order_transmission_attempted is False
    assert report.position_modification_attempted is False
