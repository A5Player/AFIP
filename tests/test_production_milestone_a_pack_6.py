from afip.intelligence.market_regime_consistency_index import MarketRegimeConsistencyIndex
from afip.intelligence.portfolio_maturity_index import PortfolioMaturityIndex
from afip.learning.optimization_drift_index import OptimizationDriftIndex
from afip.runtime.production_milestone_a_maturity_runtime import ProductionMilestoneAMaturityRuntime


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
        "portfolio_state": {
            "open_exposure": 0.35,
            "maximum_exposure": 1.0,
            "equity_growth": 12.0,
            "realized_profit_factor": 1.45,
            "drawdown_percent": 4.0,
            "allocation_diversity": 82.0,
        },
    }


def test_a1_pack_6_portfolio_maturity_index_advanced_ready():
    result = PortfolioMaturityIndex().evaluate(_context()["portfolio_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["maturity_tier"] in {"STANDARD", "ADVANCED"}
    assert result["blockers"] == []


def test_a1_pack_6_portfolio_maturity_index_observes_drawdown_pressure():
    state = dict(_context()["portfolio_state"])
    state["drawdown_percent"] = 24.0
    result = PortfolioMaturityIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "drawdown_quality_below_production_threshold" in result["blockers"]


def test_a2_pack_6_market_regime_consistency_index_ready_for_stable_regime():
    result = MarketRegimeConsistencyIndex().evaluate(_context()["regime_history"]).to_dict()

    assert result["status"] == "READY"
    assert result["dominant_regime"] == "TRENDING"
    assert result["market_state"] == "CONSISTENT"
    assert result["production_ready"] is True


def test_a2_pack_6_market_regime_consistency_index_observes_variable_regime():
    history = [{"regime": "TRENDING"}, {"regime": "RANGING"}, {"regime": "VOLATILE"}, {"regime": "TRENDING"}]
    result = MarketRegimeConsistencyIndex().evaluate(history).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["market_state"] == "VARIABLE"
    assert "regime_transition_frequency_high" in result["blockers"]


def test_a3_pack_6_optimization_drift_index_allows_stable_parameters():
    context = _context()
    result = OptimizationDriftIndex().evaluate(context["optimization_parameters"], context["baseline_parameters"]).to_dict()

    assert result["status"] == "READY"
    assert result["optimization_allowed"] is True
    assert result["drift_status"] in {"STABLE", "MODERATE"}


def test_a3_pack_6_optimization_drift_index_observes_elevated_parameter_delta():
    baseline = _context()["baseline_parameters"]
    current = {"entry_threshold": 88, "position_threshold": 80, "learning_rate": 0.15, "calibration_factor": 1.35}
    result = OptimizationDriftIndex().evaluate(current, baseline).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["optimization_allowed"] is False
    assert "optimization_drift_score_high" in result["blockers"]


def test_a4_pack_6_maturity_runtime_allows_full_quality_context():
    result = ProductionMilestoneAMaturityRuntime().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["blockers"] == []


def test_a4_pack_6_maturity_runtime_observes_regime_inconsistency():
    context = _context()
    context["regime_history"] = [{"regime": "TRENDING"}, {"regime": "RANGING"}, {"regime": "VOLATILE"}, {"regime": "LOW_LIQUIDITY"}]
    result = ProductionMilestoneAMaturityRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("regime_consistency:") for item in result["blockers"])
