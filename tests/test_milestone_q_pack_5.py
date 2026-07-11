from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_stability_validation import MarketIntentStabilityValidationRuntime


def _report(index: int, **overrides):
    payload = {
        "statistics_id": f"QSTA-{index:016X}", "status": "READY", "milestone": "Q", "pack": "4",
        "sample_start_timestamp": 10000 + index * 2000, "sample_end_timestamp": 11000 + index * 2000,
        "sequence_count": 4, "total_transition_count": 12,
        "weighted_persistence_ratio": 0.72 + index * 0.02,
        "weighted_average_intent_intensity": 0.66 + index * 0.02,
        "intent_change_rate": 0.22 + index * 0.01, "direction_change_rate": 0.20 + index * 0.01,
        "regime_change_rate": 0.10, "behaviour_change_rate": 0.12,
        "dominant_sequence_pattern": "PERSISTENT_INTENT",
        "data_quality_certified": True, "future_safe": True,
        "market_regime_before_intent": True, "market_behaviour_before_intent": True,
        "policy_version": "AFIP_V1_FEATURE_FREEZE", "broker": "XM", "symbol": "GOLD#",
        "base_lot_per_unit": 0.01, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False, "live_execution_enabled": False,
        "automatic_parameter_update_allowed": False, "trading_logic_change_allowed": False,
        "production_knowledge_allowed": False,
    }
    payload.update(overrides)
    return payload


def test_ready_stability_validation_calculates_ranges_score_and_band():
    report = MarketIntentStabilityValidationRuntime().evaluate([_report(1), _report(2), _report(3)])
    assert report.status == "READY"
    assert report.validation_id.startswith("QSTB-")
    assert report.statistics_window_count == 3
    assert report.total_sequence_count == 12
    assert report.persistence_range == 0.04
    assert report.dominant_pattern_consistency == 1.0
    assert report.stable_window_ratio == 1.0
    assert report.stability_band == "HIGH"


def test_report_is_deterministic_and_immutable():
    runtime = MarketIntentStabilityValidationRuntime()
    rows = [_report(1), _report(2), _report(3)]
    first = runtime.evaluate(rows)
    assert first == runtime.evaluate(rows)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_insufficient_sample_and_invalid_lineage():
    report = MarketIntentStabilityValidationRuntime().evaluate([_report(1), _report(2, status="BLOCKED")])
    assert "insufficient_stability_sample" in report.block_reasons
    assert "pack_4_statistics_lineage_invalid" in report.block_reasons


def test_blocks_duplicate_ids_and_overlapping_chronology():
    duplicate = _report(1)
    report = MarketIntentStabilityValidationRuntime().evaluate([duplicate, dict(duplicate), _report(3)])
    assert "stability_chronology_invalid" in report.block_reasons


def test_blocks_invalid_coverage_and_metric_ranges():
    report = MarketIntentStabilityValidationRuntime().evaluate([
        _report(1), _report(2, sequence_count=2, weighted_persistence_ratio=1.2), _report(3)
    ])
    assert "statistics_coverage_invalid" in report.block_reasons
    assert "stability_metrics_invalid" in report.block_reasons


def test_blocks_unstable_statistics_windows():
    report = MarketIntentStabilityValidationRuntime().evaluate([
        _report(1, weighted_persistence_ratio=0.10, dominant_sequence_pattern="PERSISTENT_INTENT"),
        _report(2, weighted_persistence_ratio=0.90, dominant_sequence_pattern="OSCILLATING_INTENT"),
        _report(3, weighted_persistence_ratio=0.20, dominant_sequence_pattern="MIXED_INTENT_SEQUENCE"),
    ])
    assert "market_intent_stability_threshold_not_met" in report.block_reasons
    assert report.stability_thresholds_valid is False


def test_blocks_quality_future_and_prerequisite_failures():
    report = MarketIntentStabilityValidationRuntime().evaluate([
        _report(1), _report(2, data_quality_certified=False, future_safe=False,
                               market_regime_before_intent=False, market_behaviour_before_intent=False), _report(3)
    ])
    assert "data_quality_not_certified" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons
    assert "market_regime_not_evaluated_before_intent" in report.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in report.block_reasons


def test_policy_and_execution_authority_remain_locked():
    blocked = MarketIntentStabilityValidationRuntime().evaluate([_report(1), _report(2), _report(3, broker="OTHER")])
    assert "feature_freeze_or_execution_policy_violation" in blocked.block_reasons
    report = MarketIntentStabilityValidationRuntime().evaluate([_report(1), _report(2), _report(3)])
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
