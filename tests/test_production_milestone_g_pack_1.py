from afip.runtime_observability import RuntimeObservabilityObservation, RuntimeObservabilityRuntime


def _record(**overrides):
    value = {
        "market_regime": "TREND",
        "signal_context": "SELL_CONTINUATION",
        "decision_latency_ms": 24.0,
        "engine_latency_ms": 36.0,
        "validation_latency_ms": 12.0,
        "report_latency_ms": 8.0,
        "memory_usage_mb": 128.0,
        "data_quality": 86,
        "knowledge_quality": 84,
        "strategy_quality": 82,
        "validation_quality": 81,
        "production_readiness_score": 83,
        "explainability_quality": 88,
        "metrics_quality": 90,
        "monitoring_quality": 85,
    }
    value.update(overrides)
    return value


def test_runtime_observability_blocks_records_without_market_regime():
    profile = RuntimeObservabilityRuntime().evaluate_one(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.review_required is True
    assert profile.reason == "market_regime_required"


def test_runtime_observability_preserves_regime_before_signal_context():
    reports = RuntimeObservabilityRuntime().explain_many([
        _record(market_regime="RANGE", signal_context="BUY_PULLBACK"),
        _record(market_regime="TREND", signal_context="SELL_CONTINUATION"),
    ])

    assert reports[0].market_regime == "RANGE"
    assert reports[0].signal_context == "BUY_PULLBACK"
    assert reports[1].market_regime == "TREND"
    assert reports[1].signal_context == "SELL_CONTINUATION"


def test_runtime_observability_calculates_score_deterministically():
    profile = RuntimeObservabilityRuntime().evaluate_one(_record())

    assert profile.latency_score == 0.68
    assert profile.memory_score == 0.75
    assert profile.evidence_quality == 0.8455
    assert profile.observability_score == 0.8111
    assert profile.status == "READY"


def test_runtime_observability_requires_review_for_low_metrics_quality():
    profile = RuntimeObservabilityRuntime().evaluate_one(_record(metrics_quality=40, monitoring_quality=82))

    assert profile.status == "REVIEW"
    assert profile.review_required is True
    assert profile.reason == "runtime_metrics_review_required"


def test_runtime_observability_explainability_report_contains_decision_reason():
    report = RuntimeObservabilityRuntime().explain_one(_record())
    text = report.as_text()

    assert "Market regime: TREND" in text
    assert "Runtime observability score: 0.8111" in text
    assert "Decision reason: runtime_observability_ready" in text


def test_runtime_observability_observation_normalizes_percent_values():
    observation = RuntimeObservabilityObservation.from_mapping(_record(data_quality=75, explainability_quality=65))

    assert observation.data_quality == 0.75
    assert observation.explainability_quality == 0.65
    assert observation.total_latency_ms == 80.0
