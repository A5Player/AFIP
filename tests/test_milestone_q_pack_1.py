from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_intelligence_foundation import MarketIntentIntelligenceFoundationRuntime


def _payload(**overrides):
    payload = {
        "observed_timestamp": 3000,
        "source_timestamp": 2900,
        "market_regime": "TREND",
        "market_behaviour": "DIRECTIONAL_PERSISTENCE",
        "market_regime_evaluated_first": True,
        "market_behaviour_evaluated_first": True,
        "direction": "BUY",
        "directional_pressure": 0.82,
        "liquidity_pressure": 0.45,
        "breakout_pressure": 0.55,
        "reversal_pressure": 0.18,
        "participation_strength": 0.74,
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


def test_ready_observation_classifies_buying_pressure():
    report = MarketIntentIntelligenceFoundationRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.intent_state == "BUYING_PRESSURE"
    assert report.observation_id.startswith("QINT-")


def test_observation_is_deterministic_and_immutable():
    runtime = MarketIntentIntelligenceFoundationRuntime()
    first = runtime.evaluate_one(_payload())
    second = runtime.evaluate_one(_payload())
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_future_leakage_and_invalid_chronology():
    report = MarketIntentIntelligenceFoundationRuntime().evaluate_one(
        _payload(future_leakage_detected=True, observed_timestamp=2800)
    )
    assert "future_leakage_detected" in report.block_reasons
    assert "intent_observation_chronology_invalid" in report.block_reasons


def test_blocks_when_required_evaluation_order_is_missing():
    report = MarketIntentIntelligenceFoundationRuntime().evaluate_one(
        _payload(market_regime_evaluated_first=False, market_behaviour_evaluated_first=False)
    )
    assert "market_regime_not_evaluated_before_intent" in report.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in report.block_reasons


def test_blocks_invalid_metrics_and_non_finite_values():
    report = MarketIntentIntelligenceFoundationRuntime().evaluate_one(
        _payload(directional_pressure=1.5, liquidity_pressure=float("inf"))
    )
    assert "intent_metrics_invalid" in report.block_reasons


def test_classifies_sell_breakout_reversal_and_liquidity_states():
    runtime = MarketIntentIntelligenceFoundationRuntime()
    sell = runtime.evaluate_one(_payload(direction="SELL", directional_pressure=0.78))
    breakout = runtime.evaluate_one(_payload(breakout_pressure=0.86, participation_strength=0.75))
    reversal = runtime.evaluate_one(_payload(reversal_pressure=0.88, breakout_pressure=0.30))
    liquidity = runtime.evaluate_one(
        _payload(
            market_behaviour="RANGE_ROTATION",
            direction="FLAT",
            directional_pressure=0.30,
            liquidity_pressure=0.82,
            breakout_pressure=0.25,
        )
    )
    assert sell.intent_state == "SELLING_PRESSURE"
    assert breakout.intent_state == "BREAKOUT_ATTEMPT"
    assert reversal.intent_state == "REVERSAL_ATTEMPT"
    assert liquidity.intent_state == "LIQUIDITY_SEEKING"


def test_blocks_data_quality_and_policy_violation():
    report = MarketIntentIntelligenceFoundationRuntime().evaluate_one(
        _payload(data_quality_certified=False, broker="OTHER")
    )
    assert "data_quality_not_certified" in report.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in report.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    report = MarketIntentIntelligenceFoundationRuntime().evaluate_one(_payload())
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
