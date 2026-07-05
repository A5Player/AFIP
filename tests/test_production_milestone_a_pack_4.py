from afip.intelligence.regime_risk_budget import RegimeRiskBudget
from afip.intelligence.signal_quality_auditor import SignalQualityAuditor
from afip.learning.optimization_parameter_governor import OptimizationParameterGovernor
from afip.runtime.production_milestone_a_production_control import ProductionMilestoneAProductionControl


def _samples(points=120, count=8, group="trend"):
    return [
        {"group": group, "outcome": "WIN", "entry_score": 78, "position_confidence": 74, "net_points": points}
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
        "cost_quality": {"spread_quality": 92},
    }


def test_a1_pack_4_signal_quality_audit_ready_for_consistent_signals():
    result = SignalQualityAuditor().audit(_context()["signals"]).to_dict()

    assert result["status"] == "READY"
    assert result["dominant_side"] == "BUY"
    assert result["accepted_signals"] == 3
    assert result["side_consistency"] == 100.0


def test_a1_pack_4_signal_quality_audit_observes_mixed_low_quality():
    signals = [
        {"name": "weak_buy", "group": "trend", "side": "BUY", "score": 45, "confidence": 40, "weight": 1.0},
        {"name": "weak_sell", "group": "trend", "side": "SELL", "score": 44, "confidence": 41, "weight": 1.0},
    ]
    result = SignalQualityAuditor().audit(signals).to_dict()

    assert result["status"] == "OBSERVE"
    assert "no_qualified_adaptive_signals" in result["blockers"]


def test_a2_pack_4_regime_risk_budget_standard_for_stable_trend():
    result = RegimeRiskBudget().evaluate(
        {"regime": "TRENDING", "confidence": 82},
        {"exposure_multiplier": 1.0},
        {"stability_score": 86},
    ).to_dict()

    assert result["status"] == "READY"
    assert result["risk_budget_level"] == "STANDARD"
    assert result["risk_budget_multiplier"] == 1.0


def test_a2_pack_4_regime_risk_budget_protects_high_volatility():
    result = RegimeRiskBudget().evaluate(
        {"regime": "HIGH_VOLATILITY", "confidence": 85},
        {"exposure_multiplier": 0.0},
        {"stability_score": 82},
    ).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["risk_budget_level"] == "PROTECTED"
    assert "protective_market_regime" in result["blockers"]


def test_a3_pack_4_optimization_governor_approves_bounded_parameters():
    result = OptimizationParameterGovernor().govern(
        {"entry_threshold": 70, "position_threshold": 62, "learning_rate": 0.05, "requested_adjustment": 1.0},
        {"stability_score": 84},
        {"risk_budget_multiplier": 1.0},
    ).to_dict()

    assert result["status"] == "READY"
    assert result["approved"] is True
    assert result["adjustment_limit"] == 2.0


def test_a3_pack_4_optimization_governor_blocks_unbounded_learning_rate():
    result = OptimizationParameterGovernor().govern(
        {"entry_threshold": 70, "position_threshold": 62, "learning_rate": 0.5, "requested_adjustment": 1.0},
        {"stability_score": 84},
        {"risk_budget_multiplier": 1.0},
    ).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["approved"] is False
    assert "learning_rate_out_of_bounds" in result["blockers"]


def test_a4_pack_4_production_control_allows_full_aligned_context():
    result = ProductionMilestoneAProductionControl().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["risk_budget_level"] == "STANDARD"
    assert result["blockers"] == []


def test_a4_pack_4_production_control_blocks_signal_quality_failure():
    context = _context()
    context["signals"] = [{"name": "weak_signal", "group": "trend", "side": "BUY", "score": 35, "confidence": 40, "weight": 1.0}]
    result = ProductionMilestoneAProductionControl().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any(item.startswith("signal_audit:") for item in result["blockers"])
