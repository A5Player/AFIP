from dataclasses import FrozenInstanceError

import pytest

from afip.market_intent_drift_detection import MarketIntentDriftDetectionRuntime


def _report(index: int, **overrides):
    payload = {
        "validation_id": f"QSTB-{index:016X}", "status": "READY", "milestone": "Q", "pack": "5",
        "validation_start_timestamp": 20000 + index * 3000,
        "validation_end_timestamp": 21000 + index * 3000,
        "weighted_persistence_mean": 0.74 + index * 0.01,
        "weighted_intensity_mean": 0.68 + index * 0.01,
        "stability_score": 0.90 - index * 0.01,
        "stable_window_ratio": 1.0,
        "dominant_pattern_consistency": 1.0,
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


def test_ready_drift_detection_reports_low_drift_within_tolerance():
    report = MarketIntentDriftDetectionRuntime().evaluate([_report(1), _report(2), _report(3)])
    assert report.status == "READY"
    assert report.drift_id.startswith("QDRF-")
    assert report.validation_window_count == 3
    assert report.drift_band == "LOW"
    assert report.drift_detected is False
    assert report.review_required is False


def test_report_is_deterministic_and_immutable():
    runtime = MarketIntentDriftDetectionRuntime()
    rows = [_report(1), _report(2), _report(3)]
    first = runtime.evaluate(rows)
    assert first == runtime.evaluate(rows)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_detects_high_drift_and_requires_review():
    report = MarketIntentDriftDetectionRuntime().evaluate([
        _report(1, weighted_persistence_mean=0.90, weighted_intensity_mean=0.90, stability_score=0.95),
        _report(2, weighted_persistence_mean=0.50, weighted_intensity_mean=0.45, stability_score=0.50),
        _report(3, weighted_persistence_mean=0.10, weighted_intensity_mean=0.10, stability_score=0.10,
                stable_window_ratio=0.20, dominant_pattern_consistency=0.20),
    ])
    assert report.drift_band == "HIGH"
    assert report.drift_detected is True
    assert report.review_required is True
    assert report.reason == "MARKET_INTENT_DRIFT_DETECTED"


def test_blocks_insufficient_sample_and_invalid_lineage():
    report = MarketIntentDriftDetectionRuntime().evaluate([_report(1), _report(2, status="BLOCKED")])
    assert "insufficient_drift_sample" in report.block_reasons
    assert "pack_5_stability_lineage_invalid" in report.block_reasons


def test_blocks_duplicate_ids_and_overlapping_chronology():
    duplicate = _report(1)
    report = MarketIntentDriftDetectionRuntime().evaluate([duplicate, dict(duplicate), _report(3)])
    assert "drift_chronology_invalid" in report.block_reasons


def test_blocks_invalid_metric_ranges():
    report = MarketIntentDriftDetectionRuntime().evaluate([
        _report(1), _report(2, stability_score=1.2), _report(3)
    ])
    assert "drift_metrics_invalid" in report.block_reasons


def test_blocks_quality_future_and_prerequisite_failures():
    report = MarketIntentDriftDetectionRuntime().evaluate([
        _report(1), _report(2, data_quality_certified=False, future_safe=False,
                               market_regime_before_intent=False, market_behaviour_before_intent=False), _report(3)
    ])
    assert "data_quality_not_certified" in report.block_reasons
    assert "future_leakage_detected" in report.block_reasons
    assert "market_regime_not_evaluated_before_intent" in report.block_reasons
    assert "market_behaviour_not_evaluated_before_intent" in report.block_reasons


def test_policy_and_execution_authority_remain_locked():
    blocked = MarketIntentDriftDetectionRuntime().evaluate([_report(1), _report(2), _report(3, broker="OTHER")])
    assert "feature_freeze_or_execution_policy_violation" in blocked.block_reasons
    report = MarketIntentDriftDetectionRuntime().evaluate([_report(1), _report(2), _report(3)])
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
