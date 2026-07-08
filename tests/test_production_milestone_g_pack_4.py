from afip.runtime.production_milestone_g_runtime_metrics_runtime import (
    evaluate_runtime_metrics_record,
    evaluate_runtime_metrics_records,
    explain_runtime_metrics_record,
)
from afip.runtime_metrics_integration import RuntimeMetricsObservation


def _record(**overrides):
    data = {
        "market_regime": "trend",
        "signal_context": "sell_edge",
        "runtime_component": "decision_pipeline",
        "feature_flag_state": "ON",
        "configuration_version": "v3",
        "decision_latency_ms": 180,
        "engine_latency_ms": 120,
        "memory_usage_mb": 160,
        "memory_limit_mb": 640,
        "cache_hit_ratio": 82,
        "event_log_score": 90,
        "observability_score": 88,
        "measurement_quality": 86,
    }
    data.update(overrides)
    return data


def test_runtime_metrics_blocks_records_without_market_regime():
    profile = evaluate_runtime_metrics_record(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_runtime_metrics_preserves_regime_before_signal_context():
    first, second = evaluate_runtime_metrics_records([
        _record(market_regime="trend", signal_context="buy_edge", decision_latency_ms=240),
        _record(market_regime="range", signal_context="sell_edge", decision_latency_ms=80),
    ])

    assert first.market_regime == "TREND"
    assert first.signal_context == "BUY_EDGE"
    assert second.market_regime == "RANGE"
    assert second.signal_context == "SELL_EDGE"


def test_runtime_metrics_calculates_scores_deterministically():
    first = evaluate_runtime_metrics_record(_record())
    second = evaluate_runtime_metrics_record(_record())

    assert first.status == "READY"
    assert first.reason == "runtime_metrics_ready"
    assert first.latency_score == second.latency_score
    assert first.resource_score == second.resource_score
    assert first.evidence_quality == second.evidence_quality


def test_runtime_metrics_requires_review_for_high_memory_usage():
    profile = evaluate_runtime_metrics_record(_record(memory_usage_mb=620, memory_limit_mb=640))

    assert profile.status == "REVIEW"
    assert profile.reason == "runtime_memory_review_required"
    assert profile.bottleneck == "MEMORY_USAGE"


def test_runtime_metrics_report_contains_bottleneck_and_reason():
    report = explain_runtime_metrics_record(_record(decision_latency_ms=300, engine_latency_ms=200))
    text = report.as_text()

    assert "Runtime Metrics Integration Report" in text
    assert "Configuration version: v3" in text
    assert "Bottleneck: NONE" in text
    assert "Decision reason: runtime_metrics_ready" in text


def test_runtime_metrics_observation_normalizes_percent_values():
    observation = RuntimeMetricsObservation.from_mapping(_record(cache_hit_ratio=75, event_log_score=80, observability_score=90))

    assert observation.cache_hit_ratio == 0.75
    assert observation.event_log_score == 0.80
    assert observation.observability_score == 0.90
    assert observation.memory_usage_ratio == 0.25
