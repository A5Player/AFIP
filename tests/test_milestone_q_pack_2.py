from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_state_normalization import MarketIntentStateNormalizationRuntime


def _payload(**overrides):
    payload = {
        "observation_id": "QINT-0123456789ABCDEF",
        "status": "READY",
        "observed_timestamp": 3000,
        "normalized_timestamp": 3100,
        "market_regime": "TREND",
        "market_behaviour": "DIRECTIONAL_PERSISTENCE",
        "intent_state": "BUYING_PRESSURE",
        "direction": "BUY",
        "directional_pressure": 0.82,
        "continuation_pressure": 0.76,
        "reversal_pressure": 0.18,
        "liquidity_seeking_pressure": 0.24,
        "breakout_pressure": 0.42,
        "data_quality_certified": True,
        "future_safe": True,
        "future_leakage_detected": False,
        "market_regime_before_intent": True,
        "market_behaviour_before_intent": True,
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


def test_ready_state_is_normalized_to_canonical_schema():
    report = MarketIntentStateNormalizationRuntime().evaluate_one(_payload())
    assert report.status == "READY"
    assert report.schema_version == "AFIP_MARKET_INTENT_STATE_V1"
    assert report.state_id.startswith("QINS-")
    assert report.dominant_pressure == "DIRECTIONAL"
    assert report.intensity_band == "HIGH"
    assert report.directional_alignment == "ALIGNED"


def test_normalization_is_deterministic_and_immutable():
    runtime = MarketIntentStateNormalizationRuntime()
    first = runtime.evaluate_one(_payload())
    second = runtime.evaluate_one(_payload())
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_pack_1_lineage():
    report = MarketIntentStateNormalizationRuntime().evaluate_one(
        _payload(observation_id="OTHER-1", status="BLOCKED")
    )
    assert "pack_1_observation_not_ready" in report.block_reasons


def test_blocks_future_leakage_and_invalid_chronology():
    report = MarketIntentStateNormalizationRuntime().evaluate_one(
        _payload(future_leakage_detected=True, normalized_timestamp=2900)
    )
    assert "future_leakage_detected" in report.block_reasons
    assert "normalization_chronology_invalid" in report.block_reasons


def test_blocks_missing_regime_and_behaviour_prerequisites():
    report = MarketIntentStateNormalizationRuntime().evaluate_one(
        _payload(
            market_regime_before_intent=False,
            market_behaviour_before_intent=False,
        )
    )
    assert "market_regime_not_evaluated_before_intent" in report.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in report.block_reasons


def test_blocks_invalid_labels_direction_alignment_and_metrics():
    report = MarketIntentStateNormalizationRuntime().evaluate_one(
        _payload(direction="SELL", directional_pressure=float("inf"))
    )
    assert "intent_labels_invalid" in report.block_reasons
    assert "intent_metrics_invalid" in report.block_reasons


def test_normalizes_dominant_pressure_balance_and_intensity():
    runtime = MarketIntentStateNormalizationRuntime()
    report = runtime.evaluate_one(
        _payload(
            intent_state="REVERSAL_ATTEMPT",
            direction="SELL",
            directional_pressure=0.35,
            continuation_pressure=0.20,
            reversal_pressure=0.74,
            liquidity_seeking_pressure=0.40,
            breakout_pressure=0.30,
        )
    )
    assert report.dominant_pressure == "REVERSAL"
    assert report.intent_intensity == 0.74
    assert report.intensity_band == "MODERATE"
    assert report.continuation_reversal_balance == -0.54
    assert report.directional_alignment == "NEUTRAL"


def test_data_policy_and_execution_authority_remain_locked():
    blocked = MarketIntentStateNormalizationRuntime().evaluate_one(
        _payload(data_quality_certified=False, broker="OTHER")
    )
    assert "data_quality_not_certified" in blocked.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in blocked.block_reasons

    report = MarketIntentStateNormalizationRuntime().evaluate_one(_payload())
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
