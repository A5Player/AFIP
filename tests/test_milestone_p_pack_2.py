from dataclasses import FrozenInstanceError
import pytest
from afip.market_behaviour_state_normalization import MarketBehaviourStateNormalizationRuntime


def _payload(**overrides):
    payload = {
        "observation_id": "PBEH-0123456789ABCDEF", "status": "READY",
        "observed_timestamp": 2000, "normalized_timestamp": 2100,
        "market_regime": "TREND", "behaviour_state": "DIRECTIONAL_PERSISTENCE",
        "direction": "BUY", "liquidity_condition": "NORMAL",
        "trend_efficiency": 0.8, "volatility_ratio": 1.2,
        "range_position": 0.75, "momentum_persistence": 0.7,
        "data_quality_certified": True, "future_safe": True,
        "future_leakage_detected": False, "market_regime_before_behaviour": True,
        "policy_version": "AFIP_V1_FEATURE_FREEZE", "broker": "XM", "symbol": "GOLD#",
        "base_lot_per_unit": 0.01, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False,
        "live_execution_enabled": False, "automatic_parameter_update_allowed": False,
        "trading_logic_change_allowed": False, "production_knowledge_allowed": False,
    }
    payload.update(overrides); return payload


def test_ready_state_is_normalized_to_canonical_schema():
    r = MarketBehaviourStateNormalizationRuntime().evaluate_one(_payload())
    assert r.status == "READY" and r.schema_version == "AFIP_MARKET_BEHAVIOUR_STATE_V1"
    assert r.state_id.startswith("PBNS-") and r.volatility_state == "NORMAL"
    assert r.range_zone == "UPPER" and r.momentum_state == "BULLISH_PERSISTENT"


def test_normalization_is_deterministic_and_immutable():
    rt = MarketBehaviourStateNormalizationRuntime(); a = rt.evaluate_one(_payload()); b = rt.evaluate_one(_payload())
    assert a == b
    with pytest.raises(FrozenInstanceError): a.status = "BLOCKED"


def test_blocks_invalid_pack_1_lineage():
    r = MarketBehaviourStateNormalizationRuntime().evaluate_one(_payload(observation_id="OTHER-1", status="BLOCKED"))
    assert "pack_1_observation_not_ready" in r.block_reasons


def test_blocks_future_leakage_and_invalid_chronology():
    r = MarketBehaviourStateNormalizationRuntime().evaluate_one(_payload(future_leakage_detected=True, normalized_timestamp=1900))
    assert "future_leakage_detected" in r.block_reasons
    assert "normalization_chronology_invalid" in r.block_reasons


def test_blocks_invalid_labels_and_metrics():
    r = MarketBehaviourStateNormalizationRuntime().evaluate_one(_payload(behaviour_state="UNKNOWN", volatility_ratio=float("inf")))
    assert "behaviour_labels_invalid" in r.block_reasons
    assert "behaviour_metrics_invalid" in r.block_reasons


def test_normalizes_volatility_range_and_momentum_states():
    rt = MarketBehaviourStateNormalizationRuntime()
    r = rt.evaluate_one(_payload(volatility_ratio=2.2, range_position=0.2, momentum_persistence=-0.8, direction="SELL"))
    assert r.volatility_state == "EXPANDING" and r.range_zone == "LOWER"
    assert r.momentum_state == "BEARISH_PERSISTENT"


def test_blocks_data_quality_regime_order_and_policy_violation():
    r = MarketBehaviourStateNormalizationRuntime().evaluate_one(_payload(data_quality_certified=False, market_regime_before_behaviour=False, broker="OTHER"))
    assert "data_quality_not_certified" in r.block_reasons
    assert "market_regime_not_evaluated_before_behaviour" in r.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in r.block_reasons


def test_adaptive_production_and_execution_authority_remain_disabled():
    r = MarketBehaviourStateNormalizationRuntime().evaluate_one(_payload())
    assert r.research_only and not r.automatic_parameter_update_allowed
    assert not r.trading_logic_change_allowed and not r.production_knowledge_allowed
    assert not r.production_certification_granted
    assert r.execution_status == "LOCKED_SIMULATION_ONLY"
    assert not r.direct_execution and not r.live_execution_enabled
    assert r.order_status == "NO_ORDER_SENT"
    assert not r.broker_request_created and not r.order_transmission_attempted and not r.position_modification_attempted
