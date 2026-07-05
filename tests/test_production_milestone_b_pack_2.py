from __future__ import annotations

from afip.fusion.adaptive_weight_engine import AdaptiveWeightEngine
from afip.fusion.intelligence_weight_matrix import IntelligenceWeightMatrix
from afip.fusion.performance_weight_adjustment import PerformanceWeightAdjustment
from afip.fusion.regime_weight_profile import RegimeWeightProfile
from afip.runtime.production_milestone_b_weight_runtime import ProductionMilestoneBWeightRuntime


def test_adaptive_weight_engine_returns_normalized_weights() -> None:
    result = AdaptiveWeightEngine().calculate([
        {"category": "TREND", "confidence": 0.90, "performance": 0.70, "reliability": 0.80},
        {"category": "LIQUIDITY", "confidence": 0.75, "performance": 0.60, "reliability": 0.70},
        {"category": "RISK", "confidence": 0.65, "performance": 0.55, "reliability": 0.90},
    ])
    assert result.status == "ADAPTIVE_WEIGHT_READY"
    assert abs(sum(result.weights.values()) - 1.0) < 0.01
    assert result.dominant_category == "TREND"


def test_adaptive_weight_engine_handles_missing_inputs() -> None:
    result = AdaptiveWeightEngine().calculate([])
    assert result.status == "ADAPTIVE_WEIGHT_REVIEW"
    assert result.weights == {}
    assert result.reason == "insufficient_intelligence_contribution"


def test_regime_weight_profile_resolves_trend_profile() -> None:
    result = RegimeWeightProfile().resolve("TREND")
    assert result.status == "REGIME_WEIGHT_PROFILE_READY"
    assert result.regime == "TREND"
    assert result.weights["TREND"] > result.weights["RISK"]


def test_regime_weight_profile_defaults_to_balanced_profile() -> None:
    result = RegimeWeightProfile().resolve("UNKNOWN")
    assert result.regime == "BALANCED"
    assert abs(sum(result.weights.values()) - 1.0) < 0.01


def test_performance_weight_adjustment_rewards_positive_attribution() -> None:
    result = PerformanceWeightAdjustment().adjust(
        {"TREND": 0.50, "RISK": 0.30, "EXECUTION": 0.20},
        {"TREND": 0.20, "RISK": -0.10},
    )
    assert result.status == "PERFORMANCE_WEIGHT_READY"
    assert result.weights["TREND"] > result.weights["RISK"]
    assert result.positive_adjustments == 1
    assert result.negative_adjustments == 1


def test_intelligence_weight_matrix_distributes_category_weights() -> None:
    result = IntelligenceWeightMatrix().build(
        {"TREND": 0.60, "RISK": 0.40},
        {"TREND": ["TrendStrengthIntelligence", "MarketIntelligenceV2"], "RISK": ["RiskIntelligence"]},
    )
    assert result.status == "INTELLIGENCE_WEIGHT_MATRIX_READY"
    assert result.matrix["TREND"]["TrendStrengthIntelligence"] == 0.30
    assert result.total_categories == 2


def test_milestone_b_weight_runtime_uses_adaptive_inputs() -> None:
    result = ProductionMilestoneBWeightRuntime().run(
        "TREND",
        [
            {"category": "TREND", "confidence": 0.92, "performance": 0.80, "reliability": 0.90},
            {"category": "LIQUIDITY", "confidence": 0.70, "performance": 0.60, "reliability": 0.75},
        ],
        {"TREND": 0.10},
    )
    assert result.status == "MILESTONE_B_WEIGHT_RUNTIME_READY"
    assert result.dominant_category == "TREND"
    assert "TREND" in result.matrix


def test_milestone_b_weight_runtime_falls_back_to_regime_profile() -> None:
    result = ProductionMilestoneBWeightRuntime().run("NEWS", [], {})
    assert result.status == "MILESTONE_B_WEIGHT_RUNTIME_READY"
    assert result.regime == "NEWS"
    assert result.dominant_category in {"RISK", "EXECUTION"}
