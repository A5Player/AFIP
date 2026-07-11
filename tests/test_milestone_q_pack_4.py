from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_statistics import MarketIntentStatisticsRuntime


def _report(index: int, **overrides):
    payload = {
        "sequence_id": f"QSEQ-{index:016X}",
        "status": "READY",
        "milestone": "Q",
        "pack": "3",
        "sequence_start_timestamp": 5000 + index * 1000,
        "sequence_end_timestamp": 5500 + index * 1000,
        "observation_count": 3,
        "transition_count": 2,
        "intent_change_count": index % 2,
        "direction_change_count": index % 2,
        "regime_change_count": 0,
        "behaviour_change_count": 0,
        "persistence_ratio": 1.0 if index % 2 == 0 else 0.5,
        "average_intent_intensity": 0.70 + index * 0.02,
        "intensity_change": 0.02 * index,
        "continuation_reversal_balance_change": 0.01 * index,
        "sequence_pattern": "PERSISTENT_INTENT" if index != 3 else "INTENT_REVERSAL_SEQUENCE",
        "data_quality_certified": True,
        "future_safe": True,
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


def test_ready_statistics_calculate_weighted_metrics_and_distribution():
    report = MarketIntentStatisticsRuntime().evaluate([_report(1), _report(2), _report(3)])
    assert report.status == "READY"
    assert report.statistics_id.startswith("QSTA-")
    assert report.sequence_count == 3
    assert report.total_observation_count == 9
    assert report.total_transition_count == 6
    assert report.intent_change_rate == pytest.approx(2 / 6, abs=1e-6)
    assert report.dominant_sequence_pattern == "PERSISTENT_INTENT"
    assert report.sequence_pattern_distribution == (("PERSISTENT_INTENT", 2), ("INTENT_REVERSAL_SEQUENCE", 1))


def test_statistics_are_deterministic_and_immutable():
    runtime = MarketIntentStatisticsRuntime()
    rows = [_report(1), _report(2), _report(3)]
    first = runtime.evaluate(rows)
    second = runtime.evaluate(rows)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_insufficient_sample_and_invalid_lineage():
    report = MarketIntentStatisticsRuntime().evaluate([_report(1), _report(2, status="BLOCKED")])
    assert "insufficient_statistical_sample" in report.block_reasons
    assert "pack_3_sequence_lineage_invalid" in report.block_reasons


def test_blocks_duplicate_or_non_increasing_chronology():
    duplicate = _report(1)
    report = MarketIntentStatisticsRuntime().evaluate([duplicate, dict(duplicate), _report(3)])
    assert "statistics_chronology_invalid" in report.block_reasons


def test_blocks_invalid_count_relationships_and_metrics():
    report = MarketIntentStatisticsRuntime().evaluate([
        _report(1),
        _report(2, transition_count=5, persistence_ratio=1.5),
        _report(3),
    ])
    assert "sequence_count_metrics_invalid" in report.block_reasons
    assert "sequence_statistics_metrics_invalid" in report.block_reasons


def test_calculates_population_standard_deviation_and_mean_changes():
    report = MarketIntentStatisticsRuntime().evaluate([
        _report(1, intensity_change=0.0, continuation_reversal_balance_change=-0.1),
        _report(2, intensity_change=0.1, continuation_reversal_balance_change=0.0),
        _report(3, intensity_change=0.2, continuation_reversal_balance_change=0.1),
    ])
    assert report.mean_intensity_change == 0.1
    assert report.mean_continuation_reversal_balance_change == 0.0
    assert report.intensity_change_standard_deviation == pytest.approx(0.08165, abs=1e-6)


def test_blocks_quality_future_and_prerequisite_failures():
    report = MarketIntentStatisticsRuntime().evaluate([
        _report(1),
        _report(2, data_quality_certified=False, future_safe=False,
                market_regime_before_intent=False, market_behaviour_before_intent=False),
        _report(3),
    ])
    assert "data_quality_not_certified" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons
    assert "market_regime_not_evaluated_before_intent" in report.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in report.block_reasons


def test_policy_and_execution_authority_remain_locked():
    blocked = MarketIntentStatisticsRuntime().evaluate([_report(1), _report(2), _report(3, broker="OTHER")])
    assert "feature_freeze_or_execution_policy_violation" in blocked.block_reasons
    report = MarketIntentStatisticsRuntime().evaluate([_report(1), _report(2), _report(3)])
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
