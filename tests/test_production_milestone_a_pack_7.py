from afip.intelligence.capital_preservation_index import CapitalPreservationIndex
from afip.intelligence.market_participation_quality import MarketParticipationQuality
from afip.learning.learning_confidence_interval import LearningConfidenceInterval
from afip.runtime.production_milestone_a_capital_runtime import ProductionMilestoneACapitalRuntime


def _samples(points=120, count=8, outcome="WIN"):
    return [
        {"group": "trend", "outcome": outcome, "entry_score": 78, "position_confidence": 74, "net_points": points}
        for _ in range(count)
    ]


def _context():
    return {
        "signals": [
            {"name": "trend_quality", "group": "trend", "side": "BUY", "score": 78, "confidence": 84, "weight": 1.0},
            {"name": "structure_quality", "group": "trend", "side": "BUY", "score": 76, "confidence": 82, "weight": 1.0},
            {"name": "liquidity_quality", "group": "trend", "side": "BUY", "score": 74, "confidence": 79, "weight": 1.0},
        ],
        "learning_samples": _samples(),
        "regime_features": {"trend_strength": 80, "volatility_score": 54, "liquidity_score": 88, "spread_quality": 90, "structure_quality": 76},
        "regime_history": [{"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}],
        "base_thresholds": {"entry_threshold": 70, "position_threshold": 62, "learning_rate": 0.05, "calibration_factor": 1.0},
        "baseline_parameters": {"entry_threshold": 70, "position_threshold": 62, "learning_rate": 0.05, "calibration_factor": 1.0},
        "optimization_parameters": {"entry_threshold": 71, "position_threshold": 63, "learning_rate": 0.05, "calibration_factor": 1.02, "requested_adjustment": 1.0},
        "calibration_group": "trend",
        "allocation_group": "trend",
        "quality_factors": {"base_weight": 1.0, "win_rate": 72, "stability": 78, "drawdown_control": 80, "sample_quality": 85},
        "cost_quality": {"spread_quality": 92, "slippage_quality": 88},
        "liquidity_quality": {"liquidity_score": 86, "fill_probability": 84},
        "decision_quality": {"confidence": 86, "signal_consistency": 100},
        "execution_state": {
            "spread_quality": 92,
            "slippage_quality": 88,
            "liquidity_score": 86,
            "fill_probability": 84,
            "signal_consistency": 96,
            "decision_confidence": 86,
        },
        "portfolio_state": {
            "open_exposure": 0.35,
            "maximum_exposure": 1.0,
            "equity_growth": 12.0,
            "realized_profit_factor": 1.45,
            "drawdown_percent": 4.0,
            "intraday_drawdown_percent": 3.0,
            "equity_volatility_percent": 4.0,
            "recovery_factor": 1.45,
            "allocation_diversity": 82.0,
        },
    }


def test_a1_pack_7_capital_preservation_index_ready_for_resilient_capital():
    result = CapitalPreservationIndex().evaluate(_context()["portfolio_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["capital_state"] in {"STABLE", "RESILIENT"}
    assert result["blockers"] == []


def test_a1_pack_7_capital_preservation_index_observes_excessive_drawdown():
    state = dict(_context()["portfolio_state"])
    state["drawdown_percent"] = 22.0
    result = CapitalPreservationIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "drawdown_above_capital_preservation_threshold" in result["blockers"]


def test_a2_pack_7_market_participation_quality_ready_for_efficient_execution():
    result = MarketParticipationQuality().evaluate(_context()["execution_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["participation_state"] in {"ACCEPTABLE", "EFFICIENT"}
    assert result["blockers"] == []


def test_a2_pack_7_market_participation_quality_observes_low_liquidity_access():
    state = dict(_context()["execution_state"])
    state["liquidity_score"] = 35.0
    state["fill_probability"] = 42.0
    result = MarketParticipationQuality().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "liquidity_access_below_production_threshold" in result["blockers"]


def test_a3_pack_7_learning_confidence_interval_allows_sufficient_samples():
    result = LearningConfidenceInterval().evaluate(_context()["learning_samples"]).to_dict()

    assert result["status"] == "READY"
    assert result["optimization_allowed"] is True
    assert result["confidence_state"] in {"STANDARD_CONFIDENCE", "HIGH_CONFIDENCE"}


def test_a3_pack_7_learning_confidence_interval_observes_insufficient_depth():
    result = LearningConfidenceInterval().evaluate(_samples(count=2)).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["optimization_allowed"] is False
    assert "learning_sample_depth_below_production_threshold" in result["blockers"]


def test_a4_pack_7_capital_runtime_allows_full_quality_context():
    result = ProductionMilestoneACapitalRuntime().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["blockers"] == []


def test_a4_pack_7_capital_runtime_observes_capital_pressure():
    context = _context()
    context["portfolio_state"] = dict(context["portfolio_state"])
    context["portfolio_state"]["intraday_drawdown_percent"] = 14.0
    result = ProductionMilestoneACapitalRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("capital_preservation:") for item in result["blockers"])
