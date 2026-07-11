from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_sequence_analysis import MarketIntentSequenceAnalysisRuntime


def _state(index: int, **overrides):
    payload = {
        "state_id": f"QINS-{index:016X}",
        "status": "READY",
        "schema_version": "AFIP_MARKET_INTENT_STATE_V1",
        "normalized_timestamp": 3000 + index * 100,
        "market_regime": "TREND",
        "market_behaviour": "DIRECTIONAL_PERSISTENCE",
        "intent_state": "BUYING_PRESSURE",
        "direction": "BUY",
        "intent_intensity": 0.70 + index * 0.02,
        "continuation_reversal_balance": 0.45 + index * 0.03,
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


def test_ready_sequence_reports_persistence_and_deltas():
    report = MarketIntentSequenceAnalysisRuntime().evaluate([_state(1), _state(2), _state(3)])
    assert report.status == "READY"
    assert report.sequence_id.startswith("QSEQ-")
    assert report.observation_count == 3
    assert report.transition_count == 2
    assert report.persistence_ratio == 1.0
    assert report.sequence_pattern == "PERSISTENT_INTENT"
    assert report.intensity_change == 0.04


def test_sequence_analysis_is_deterministic_and_immutable():
    runtime = MarketIntentSequenceAnalysisRuntime()
    first = runtime.evaluate([_state(1), _state(2)])
    second = runtime.evaluate([_state(1), _state(2)])
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_insufficient_sequence_and_invalid_lineage():
    report = MarketIntentSequenceAnalysisRuntime().evaluate([_state(1, status="BLOCKED")])
    assert "insufficient_sequence_length" in report.block_reasons
    assert "pack_2_state_lineage_invalid" in report.block_reasons


def test_blocks_duplicate_or_non_increasing_chronology():
    duplicate = _state(1)
    report = MarketIntentSequenceAnalysisRuntime().evaluate([duplicate, dict(duplicate)])
    assert "sequence_chronology_invalid" in report.block_reasons


def test_detects_intent_reversal_sequence():
    report = MarketIntentSequenceAnalysisRuntime().evaluate([
        _state(1),
        _state(2),
        _state(3, intent_state="REVERSAL_ATTEMPT", direction="SELL"),
    ])
    assert report.intent_change_count == 1
    assert report.direction_change_count == 1
    assert report.sequence_pattern == "INTENT_REVERSAL_SEQUENCE"


def test_detects_oscillating_sequence():
    report = MarketIntentSequenceAnalysisRuntime().evaluate([
        _state(1),
        _state(2, intent_state="SELLING_PRESSURE", direction="SELL"),
        _state(3, intent_state="BUYING_PRESSURE", direction="BUY"),
        _state(4, intent_state="SELLING_PRESSURE", direction="SELL"),
    ])
    assert report.sequence_pattern == "OSCILLATING_INTENT"
    assert report.direction_change_count == 3


def test_blocks_quality_future_and_prerequisite_failures():
    report = MarketIntentSequenceAnalysisRuntime().evaluate([
        _state(1),
        _state(2, data_quality_certified=False, future_leakage_detected=True,
               market_regime_before_intent=False, market_behaviour_before_intent=False),
    ])
    assert "data_quality_not_certified" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons
    assert "market_regime_not_evaluated_before_intent" in report.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in report.block_reasons


def test_policy_and_execution_authority_remain_locked():
    blocked = MarketIntentSequenceAnalysisRuntime().evaluate([_state(1), _state(2, broker="OTHER")])
    assert "feature_freeze_or_execution_policy_violation" in blocked.block_reasons
    report = MarketIntentSequenceAnalysisRuntime().evaluate([_state(1), _state(2)])
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
