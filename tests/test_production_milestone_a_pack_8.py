from afip.intelligence.allocation_discipline_index import AllocationDisciplineIndex
from afip.intelligence.liquidity_efficiency_index import LiquidityEfficiencyIndex
from afip.learning.learning_efficiency_score import LearningEfficiencyScore
from afip.runtime.production_milestone_a_efficiency_runtime import ProductionMilestoneAEfficiencyRuntime


def _samples(points=120, count=8, outcome="WIN"):
    return [
        {
            "group": "trend",
            "outcome": outcome,
            "entry_score": 78,
            "position_confidence": 74,
            "confidence": 82,
            "stability_score": 80,
            "net_points": points,
        }
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
            "execution_cost_quality": 88,
            "liquidity_score": 86,
            "depth_quality": 84,
            "fill_probability": 84,
            "signal_consistency": 96,
            "decision_confidence": 86,
        },
        "portfolio_state": {
            "open_exposure": 0.35,
            "maximum_exposure": 1.0,
            "concentration_risk": 32.0,
            "equity_growth": 12.0,
            "realized_profit_factor": 1.45,
            "drawdown_percent": 4.0,
            "intraday_drawdown_percent": 3.0,
            "equity_volatility_percent": 4.0,
            "recovery_factor": 1.45,
            "allocation_diversity": 82.0,
        },
    }


def test_a1_pack_8_liquidity_efficiency_index_ready_for_efficient_market_access():
    result = LiquidityEfficiencyIndex().evaluate(_context()["execution_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["efficiency_state"] in {"STANDARD_EFFICIENCY", "HIGH_EFFICIENCY"}
    assert result["blockers"] == []


def test_a1_pack_8_liquidity_efficiency_index_observes_low_fill_probability():
    state = dict(_context()["execution_state"])
    state["fill_probability"] = 34.0
    result = LiquidityEfficiencyIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "fill_probability_below_liquidity_efficiency_threshold" in result["blockers"]


def test_a2_pack_8_allocation_discipline_index_ready_for_balanced_exposure():
    result = AllocationDisciplineIndex().evaluate(_context()["portfolio_state"]).to_dict()

    assert result["status"] == "READY"
    assert result["production_ready"] is True
    assert result["discipline_state"] in {"STANDARD_DISCIPLINE", "HIGH_DISCIPLINE"}
    assert result["blockers"] == []


def test_a2_pack_8_allocation_discipline_index_observes_excessive_exposure():
    state = dict(_context()["portfolio_state"])
    state["open_exposure"] = 0.98
    result = AllocationDisciplineIndex().evaluate(state).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_ready"] is False
    assert "exposure_utilization_above_allocation_discipline_threshold" in result["blockers"]


def test_a3_pack_8_learning_efficiency_score_allows_consistent_learning():
    result = LearningEfficiencyScore().evaluate(_samples()).to_dict()

    assert result["status"] == "READY"
    assert result["optimization_allowed"] is True
    assert result["efficiency_state"] in {"STANDARD_EFFICIENCY", "HIGH_EFFICIENCY"}


def test_a3_pack_8_learning_efficiency_score_observes_negative_learning_ratio():
    result = LearningEfficiencyScore().evaluate(_samples(points=-90, count=8, outcome="LOSS")).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["optimization_allowed"] is False
    assert "positive_learning_ratio_below_efficiency_threshold" in result["blockers"]


def test_a4_pack_8_efficiency_runtime_allows_full_quality_context():
    result = ProductionMilestoneAEfficiencyRuntime().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["blockers"] == []


def test_a4_pack_8_efficiency_runtime_observes_liquidity_inefficiency():
    context = _context()
    context["execution_state"] = dict(context["execution_state"])
    context["execution_state"]["spread_quality"] = 40.0
    result = ProductionMilestoneAEfficiencyRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("liquidity_efficiency:") for item in result["blockers"])
