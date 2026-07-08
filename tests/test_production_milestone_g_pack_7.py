from afip.runtime.production_milestone_g_long_run_stability_runtime import (
    evaluate_long_run_stability_record,
    evaluate_long_run_stability_records,
    explain_long_run_stability_record,
)
from afip.long_run_stability import LongRunStabilityObservation


def _record(**overrides):
    data = {
        "market_regime": "trend",
        "signal_context": "buy_edge",
        "runtime_component": "production_runtime",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "configuration_version": "v6",
        "paper_trading_score": 84,
        "production_hardening_score": 86,
        "runtime_metrics_score": 82,
        "feature_flag_score": 78,
        "repeated_runs": 12,
        "deterministic_matches": 12,
        "state_integrity_score": 91,
        "resource_trend_score": 83,
        "anomaly_rate": 4,
        "max_drawdown": 9,
    }
    data.update(overrides)
    return data


def test_long_run_stability_blocks_records_without_market_regime():
    profile = evaluate_long_run_stability_record(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_long_run_stability_blocks_live_execution_mode():
    profile = evaluate_long_run_stability_record(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_long_run_stability"
    assert profile.readiness_gate == "BLOCKED"


def test_long_run_stability_preserves_regime_before_signal_context():
    first, second = evaluate_long_run_stability_records([
        _record(market_regime="trend", signal_context="buy_edge"),
        _record(market_regime="range", signal_context="sell_edge"),
    ])

    assert first.market_regime == "TREND"
    assert first.signal_context == "BUY_EDGE"
    assert second.market_regime == "RANGE"
    assert second.signal_context == "SELL_EDGE"


def test_long_run_stability_calculates_scores_deterministically():
    first = evaluate_long_run_stability_record(_record())
    second = evaluate_long_run_stability_record(_record())

    assert first.status == "READY"
    assert first.reason == "long_run_stability_ready"
    assert first.stability_quality == second.stability_quality
    assert first.long_run_score == second.long_run_score
    assert first.readiness_gate == "LONG_RUN_STABILITY_READY"


def test_long_run_stability_requires_review_for_low_deterministic_consistency():
    profile = evaluate_long_run_stability_record(_record(deterministic_matches=8))

    assert profile.status == "REVIEW"
    assert profile.reason == "deterministic_consistency_review_required"
    assert profile.readiness_gate == "REVIEW_REQUIRED"


def test_long_run_stability_report_and_observation_normalizes_percent_values():
    observation = LongRunStabilityObservation.from_mapping(_record(paper_trading_score=75, anomaly_rate=6, max_drawdown=12))
    report = explain_long_run_stability_record(_record())
    text = report.as_text()

    assert observation.paper_trading_score == 0.75
    assert observation.anomaly_rate == 0.06
    assert observation.max_drawdown == 0.12
    assert observation.deterministic_consistency == 1.0
    assert "Long-run Stability Report" in text
    assert "Execution mode: LOCKED_SIMULATION_ONLY" in text
    assert "Readiness gate: LONG_RUN_STABILITY_READY" in text
    assert "Decision reason: long_run_stability_ready" in text
