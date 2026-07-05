from afip.intelligence.adaptive_weight_allocator import AdaptiveWeightAllocator
from afip.intelligence.regime_exposure_controller import RegimeExposureController
from afip.learning.learning_stability_monitor import LearningStabilityMonitor
from afip.runtime.production_milestone_a_decision_bridge import ProductionMilestoneADecisionBridge


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
        ],
        "learning_samples": _samples(),
        "regime_features": {"trend_strength": 80, "volatility_score": 54, "liquidity_score": 88, "spread_quality": 90, "structure_quality": 76},
        "regime_history": [{"regime": "TRENDING"}, {"regime": "TRENDING"}, {"regime": "TRENDING"}],
        "base_thresholds": {"entry_threshold": 70, "position_threshold": 62},
        "calibration_group": "trend",
        "allocation_group": "trend",
        "quality_factors": {"base_weight": 1.0, "win_rate": 72, "stability": 78, "drawdown_control": 80, "sample_quality": 85},
        "cost_quality": {"spread_quality": 92},
    }


def test_a1_pack_3_weight_profile_allocates_quality_weight():
    profile = AdaptiveWeightAllocator().build_profile(
        "trend", {"base_weight": 1.0, "win_rate": 74, "stability": 80, "drawdown_control": 82, "sample_quality": 90}
    ).to_dict()

    assert profile["status"] == "READY"
    assert profile["quality_score"] > 70
    assert profile["allocated_weight"] > 1.0


def test_a1_pack_3_weight_allocation_preserves_signal_contract():
    allocator = AdaptiveWeightAllocator()
    profile = allocator.build_profile("trend", {"base_weight": 1.0, "win_rate": 74, "stability": 80, "drawdown_control": 82, "sample_quality": 90})
    signals = allocator.allocate([{"name": "trend_quality", "group": "trend", "side": "BUY", "score": 76, "confidence": 80}], {"trend": profile})

    assert signals[0].weight == profile.allocated_weight
    assert "weight_allocation" in signals[0].metadata


def test_a2_pack_3_exposure_normal_for_stable_trending_regime():
    result = RegimeExposureController().evaluate(
        {"regime": "TRENDING", "confidence": 82, "action_bias": "FOLLOW_TREND"},
        {"risk_bias": "NORMAL_EXPOSURE"},
        {"spread_quality": 90},
    ).to_dict()

    assert result["status"] == "READY"
    assert result["exposure_level"] == "NORMAL"
    assert result["exposure_multiplier"] == 1.0


def test_a2_pack_3_exposure_blocks_high_volatility():
    result = RegimeExposureController().evaluate(
        {"regime": "HIGH_VOLATILITY", "confidence": 80, "action_bias": "HOLD"},
        {"risk_bias": "NORMAL_EXPOSURE"},
    ).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["action_bias"] == "HOLD"
    assert result["exposure_multiplier"] == 0.0


def test_a3_pack_3_learning_stability_ready_for_consistent_returns():
    result = LearningStabilityMonitor().evaluate(_samples(points=110, count=8)).to_dict()

    assert result["status"] == "READY"
    assert result["recommendation"] == "ALLOW_ADAPTIVE_ADJUSTMENT"
    assert result["stability_score"] >= 80


def test_a3_pack_3_learning_stability_waits_for_samples():
    result = LearningStabilityMonitor(minimum_samples=6).evaluate(_samples(count=2)).to_dict()

    assert result["status"] == "LEARNING"
    assert "insufficient_learning_stability_samples" in result["blockers"]


def test_a4_pack_3_decision_bridge_allows_aligned_production():
    result = ProductionMilestoneADecisionBridge().evaluate(_context()).to_dict()

    assert result["status"] == "READY"
    assert result["production_allowed"] is True
    assert result["action"] == "BUY"
    assert result["exposure_multiplier"] == 1.0
    assert result["blockers"] == []


def test_a4_pack_3_decision_bridge_blocks_protective_regime():
    context = _context()
    context["regime_features"] = {"trend_strength": 42, "volatility_score": 92, "liquidity_score": 40, "spread_quality": 80, "structure_quality": 40}
    result = ProductionMilestoneADecisionBridge().evaluate(context).to_dict()

    assert result["status"] == "OBSERVE"
    assert result["production_allowed"] is False
    assert result["action"] == "HOLD"
    assert any("enhanced_runtime" in item or "exposure_control" in item for item in result["blockers"])
