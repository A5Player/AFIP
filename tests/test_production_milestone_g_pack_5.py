from afip.runtime.production_milestone_g_production_hardening_runtime import (
    evaluate_production_hardening_record,
    evaluate_production_hardening_records,
    explain_production_hardening_record,
)
from afip.production_hardening import ProductionHardeningObservation


def _record(**overrides):
    data = {
        "market_regime": "trend",
        "signal_context": "buy_edge",
        "runtime_component": "production_runtime",
        "feature_flag_state": "ON",
        "configuration_version": "v4",
        "observability_score": 88,
        "event_log_score": 86,
        "feature_flag_score": 90,
        "runtime_metrics_score": 84,
        "dependency_alignment": 82,
        "rollback_readiness": 78,
        "monitoring_coverage": 80,
    }
    data.update(overrides)
    return data


def test_production_hardening_blocks_records_without_market_regime():
    profile = evaluate_production_hardening_record(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_production_hardening_preserves_regime_before_signal_context():
    first, second = evaluate_production_hardening_records([
        _record(market_regime="trend", signal_context="buy_edge"),
        _record(market_regime="range", signal_context="sell_edge"),
    ])

    assert first.market_regime == "TREND"
    assert first.signal_context == "BUY_EDGE"
    assert second.market_regime == "RANGE"
    assert second.signal_context == "SELL_EDGE"


def test_production_hardening_calculates_scores_deterministically():
    first = evaluate_production_hardening_record(_record())
    second = evaluate_production_hardening_record(_record())

    assert first.status == "READY"
    assert first.reason == "production_hardening_ready"
    assert first.integration_quality == second.integration_quality
    assert first.hardening_score == second.hardening_score
    assert first.readiness_gate == "PRODUCTION_READY"


def test_production_hardening_requires_review_for_low_dependency_alignment():
    profile = evaluate_production_hardening_record(_record(dependency_alignment=60))

    assert profile.status == "REVIEW"
    assert profile.reason == "dependency_alignment_review_required"
    assert profile.readiness_gate == "REVIEW_REQUIRED"


def test_production_hardening_report_contains_gate_and_reason():
    report = explain_production_hardening_record(_record())
    text = report.as_text()

    assert "Production Hardening Report" in text
    assert "Configuration version: v4" in text
    assert "Readiness gate: PRODUCTION_READY" in text
    assert "Decision reason: production_hardening_ready" in text


def test_production_hardening_observation_normalizes_percent_values():
    observation = ProductionHardeningObservation.from_mapping(_record(observability_score=75, event_log_score=80, monitoring_coverage=90))

    assert observation.observability_score == 0.75
    assert observation.event_log_score == 0.80
    assert observation.monitoring_coverage == 0.90
    assert observation.feature_flag_enabled is True
