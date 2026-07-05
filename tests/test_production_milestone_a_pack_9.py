from afip.intelligence.execution_consistency_index import ExecutionConsistencyIndex
from afip.intelligence.portfolio_resilience_index import PortfolioResilienceIndex
from afip.learning.learning_resilience_score import LearningResilienceScore
from afip.runtime.production_milestone_a_resilience_runtime import ProductionMilestoneAResilienceRuntime


def _samples(points=120, count=8, confidence=82):
    return [
        {
            "group": "trend",
            "outcome": "WIN" if points > 0 else "LOSS",
            "entry_score": 78,
            "position_confidence": confidence,
            "confidence": confidence,
            "stability_score": 80,
            "net_points": points,
        }
        for _ in range(count)
    ]


def _context():
    return {
        "action": "BUY",
        "decision_quality": {"side": "BUY", "confidence": 86, "signal_consistency": 96},
        "learning_samples": _samples(),
        "execution_state": {
            "fill_probability": 86,
            "fill_consistency": 86,
            "spread_quality": 90,
            "spread_consistency": 88,
            "slippage_quality": 84,
            "slippage_consistency": 82,
            "signal_consistency": 96,
            "decision_consistency": 94,
        },
        "portfolio_state": {
            "open_exposure": 0.42,
            "maximum_exposure": 1.0,
            "drawdown_percent": 3.0,
            "intraday_drawdown_percent": 2.0,
            "equity_volatility_percent": 4.0,
            "recovery_factor": 1.45,
        },
    }


def test_a1_pack_9_execution_consistency_index_ready_for_stable_execution():
    result = ExecutionConsistencyIndex().evaluate(_context()["execution_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["consistency_state"] in {"STANDARD_CONSISTENCY", "HIGH_CONSISTENCY"}
    assert result["blockers"] == []


def test_a1_pack_9_execution_consistency_index_observes_unstable_fill_quality():
    state = dict(_context()["execution_state"])
    state["fill_consistency"] = 35.0
    result = ExecutionConsistencyIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "fill_consistency_below_execution_threshold" in result["blockers"]


def test_a2_pack_9_portfolio_resilience_index_ready_for_normal_variance():
    result = PortfolioResilienceIndex().evaluate(_context()["portfolio_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["resilience_state"] in {"STANDARD_RESILIENCE", "HIGH_RESILIENCE"}
    assert result["blockers"] == []


def test_a2_pack_9_portfolio_resilience_index_observes_large_drawdown():
    state = dict(_context()["portfolio_state"])
    state["drawdown_percent"] = 12.0
    state["intraday_drawdown_percent"] = 8.0
    result = PortfolioResilienceIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "drawdown_resilience_below_portfolio_threshold" in result["blockers"]


def test_a3_pack_9_learning_resilience_score_allows_resilient_optimization():
    result = LearningResilienceScore().evaluate(_samples()).to_dict()

    assert result["status"] == "READY"
    assert result["optimization_allowed"] is True
    assert result["resilience_state"] in {"STANDARD_RESILIENCE", "HIGH_RESILIENCE"}


def test_a3_pack_9_learning_resilience_score_observes_negative_average_points():
    result = LearningResilienceScore().evaluate(_samples(points=-80, count=8, confidence=70)).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["optimization_allowed"] is False
    assert "average_points_below_learning_resilience_threshold" in result["blockers"]


def test_a4_pack_9_resilience_runtime_allows_consistent_context():
    result = ProductionMilestoneAResilienceRuntime().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["blockers"] == []


def test_a4_pack_9_resilience_runtime_observes_portfolio_resilience_issue():
    context = _context()
    context["portfolio_state"] = dict(context["portfolio_state"])
    context["portfolio_state"]["equity_volatility_percent"] = 14.0
    result = ProductionMilestoneAResilienceRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("portfolio_resilience:") for item in result["blockers"])
