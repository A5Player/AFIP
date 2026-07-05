from afip.intelligence.execution_quality_index import ExecutionQualityIndex
from afip.intelligence.portfolio_exposure_allocator import PortfolioExposureAllocator
from afip.learning.learning_feedback_index import LearningFeedbackIndex
from afip.runtime.production_milestone_a_portfolio_runtime import ProductionMilestoneAPortfolioRuntime


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
        "regime_history": [{"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}],
        "base_thresholds": {"entry_threshold": 70, "position_threshold": 62},
        "optimization_parameters": {"entry_threshold": 70, "position_threshold": 62, "learning_rate": 0.05, "requested_adjustment": 1.0},
        "calibration_group": "trend",
        "allocation_group": "trend",
        "quality_factors": {"base_weight": 1.0, "win_rate": 72, "stability": 78, "drawdown_control": 80, "sample_quality": 85},
        "cost_quality": {"spread_quality": 92, "slippage_quality": 88},
        "liquidity_quality": {"liquidity_score": 86, "fill_probability": 84},
        "decision_quality": {"confidence": 86, "signal_consistency": 100},
        "portfolio_state": {"open_exposure": 0.0, "maximum_exposure": 1.0},
    }


def test_a1_pack_5_execution_quality_index_ready_for_clean_execution_context():
    result = ExecutionQualityIndex().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["execution_quality_score"] >= 80.0
    assert result["blockers"] == []


def test_a1_pack_5_execution_quality_index_observes_high_cost_context():
    context = _context()
    context["cost_quality"] = {"spread_quality": 30, "slippage_quality": 35}
    result = ExecutionQualityIndex().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert "execution_cost_quality_low" in result["blockers"]


def test_a2_pack_5_portfolio_exposure_allocator_standard_allocation():
    result = PortfolioExposureAllocator().allocate(
        {"status": "READY", "risk_budget_multiplier": 1.0, "maximum_allocation_units": 1},
        {"execution_quality_score": 88},
        {"open_exposure": 0.0, "maximum_exposure": 1.0},
    ).to_dict()

    assert result["status"] == "READY"
    assert result["allocation_status"] == "STANDARD"
    assert result["exposure_units"] == 1
    assert result["capital_fraction"] == 0.01


def test_a2_pack_5_portfolio_exposure_allocator_blocks_exposure_limit():
    result = PortfolioExposureAllocator().allocate(
        {"status": "READY", "risk_budget_multiplier": 1.0, "maximum_allocation_units": 1},
        {"execution_quality_score": 88},
        {"open_exposure": 1.0, "maximum_exposure": 1.0},
    ).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["exposure_units"] == 0
    assert "portfolio_exposure_limit_reached" in result["blockers"]


def test_a3_pack_5_learning_feedback_index_positive_bias():
    result = LearningFeedbackIndex().evaluate(_samples(points=120, count=8)).to_dict()

    assert result["status"] == "READY"
    assert result["optimization_bias"] == "POSITIVE"
    assert result["positive_ratio"] == 100.0


def test_a3_pack_5_learning_feedback_index_observes_negative_feedback():
    result = LearningFeedbackIndex().evaluate(_samples(points=-80, count=8, outcome="LOSS")).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["optimization_bias"] == "DEFENSIVE"
    assert "low_positive_feedback_ratio" in result["blockers"]


def test_a4_pack_5_portfolio_runtime_allows_full_quality_context():
    result = ProductionMilestoneAPortfolioRuntime().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["exposure_units"] == 1
    assert result["blockers"] == []


def test_a4_pack_5_portfolio_runtime_observes_low_execution_quality():
    context = _context()
    context["cost_quality"] = {"spread_quality": 30, "slippage_quality": 35}
    result = ProductionMilestoneAPortfolioRuntime().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("execution_quality:") for item in result["blockers"])
