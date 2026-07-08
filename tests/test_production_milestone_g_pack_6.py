from afip.runtime.production_milestone_g_paper_trading_runtime import (
    evaluate_paper_trading_record,
    evaluate_paper_trading_records,
    explain_paper_trading_record,
)
from afip.paper_trading import PaperTradingObservation


def _record(**overrides):
    data = {
        "market_regime": "trend",
        "signal_context": "buy_edge",
        "runtime_component": "production_runtime",
        "execution_mode": "LOCKED_SIMULATION_ONLY",
        "configuration_version": "v5",
        "decision_action": "BUY",
        "decision_confidence": 82,
        "production_hardening_score": 84,
        "risk_allowed": True,
        "trading_cost_score": 76,
        "paper_account_equity": 1000,
        "simulated_lot": 0.01,
        "max_drawdown": 8,
    }
    data.update(overrides)
    return data


def test_paper_trading_blocks_records_without_market_regime():
    profile = evaluate_paper_trading_record(_record(market_regime=""))

    assert profile.status == "BLOCKED"
    assert profile.reason == "market_regime_required"


def test_paper_trading_blocks_live_execution_mode():
    profile = evaluate_paper_trading_record(_record(execution_mode="LIVE"))

    assert profile.status == "BLOCKED"
    assert profile.reason == "live_execution_not_allowed_for_paper_trading"
    assert profile.readiness_gate == "BLOCKED"


def test_paper_trading_preserves_regime_before_signal_context():
    first, second = evaluate_paper_trading_records([
        _record(market_regime="trend", signal_context="buy_edge"),
        _record(market_regime="range", signal_context="sell_edge", decision_action="SELL"),
    ])

    assert first.market_regime == "TREND"
    assert first.signal_context == "BUY_EDGE"
    assert second.market_regime == "RANGE"
    assert second.signal_context == "SELL_EDGE"


def test_paper_trading_calculates_scores_deterministically():
    first = evaluate_paper_trading_record(_record())
    second = evaluate_paper_trading_record(_record())

    assert first.status == "READY"
    assert first.reason == "paper_trading_ready"
    assert first.paper_quality == second.paper_quality
    assert first.continuity_score == second.continuity_score
    assert first.readiness_gate == "PAPER_TRADING_READY"


def test_paper_trading_requires_review_for_high_drawdown():
    profile = evaluate_paper_trading_record(_record(max_drawdown=35))

    assert profile.status == "REVIEW"
    assert profile.reason == "paper_drawdown_review_required"
    assert profile.readiness_gate == "REVIEW_REQUIRED"


def test_paper_trading_report_and_observation_normalizes_percent_values():
    observation = PaperTradingObservation.from_mapping(_record(decision_confidence=75, trading_cost_score=80, max_drawdown=12))
    report = explain_paper_trading_record(_record())
    text = report.as_text()

    assert observation.decision_confidence == 0.75
    assert observation.trading_cost_score == 0.80
    assert observation.max_drawdown == 0.12
    assert observation.simulation_only is True
    assert "Paper Trading Report" in text
    assert "Execution mode: LOCKED_SIMULATION_ONLY" in text
    assert "Readiness gate: PAPER_TRADING_READY" in text
    assert "Decision reason: paper_trading_ready" in text
