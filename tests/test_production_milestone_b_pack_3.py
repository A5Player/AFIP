from __future__ import annotations

from afip.fusion.regime_allocation_blender import RegimeAllocationBlender
from afip.fusion.regime_transition_matrix import RegimeTransitionMatrix
from afip.fusion.regime_weight_integration import RegimeWeightIntegration
from afip.fusion.volatility_weight_profile import VolatilityWeightProfile
from afip.runtime.production_milestone_b_regime_runtime import ProductionMilestoneBRegimeRuntime


def test_regime_transition_matrix_detects_continuity() -> None:
    result = RegimeTransitionMatrix().evaluate("TREND", "TREND")
    assert result.status == "REGIME_TRANSITION_READY"
    assert result.transition_risk < 0.20
    assert result.reason == "regime_continuity"


def test_regime_transition_matrix_flags_news_transition() -> None:
    result = RegimeTransitionMatrix().evaluate("TREND", "NEWS")
    assert result.transition_risk >= 0.80
    assert result.stability_score <= 0.20


def test_volatility_weight_profile_prioritizes_risk_under_extreme_volatility() -> None:
    result = VolatilityWeightProfile().resolve("EXTREME")
    assert result.status == "VOLATILITY_WEIGHT_PROFILE_READY"
    assert result.dominant_category == "RISK"
    assert result.weights["RISK"] > result.weights["TREND"]


def test_volatility_weight_profile_defaults_to_normal() -> None:
    result = VolatilityWeightProfile().resolve("UNKNOWN")
    assert result.volatility_regime == "NORMAL"
    assert abs(sum(result.weights.values()) - 1.0) < 0.01


def test_regime_allocation_blender_normalizes_weights() -> None:
    result = RegimeAllocationBlender().blend(
        {"TREND": 0.40, "MOMENTUM": 0.25, "RISK": 0.35},
        {"TREND": 0.10, "EXECUTION": 0.40, "RISK": 0.50},
        0.70,
    )
    assert result.status == "REGIME_ALLOCATION_READY"
    assert abs(sum(result.weights.values()) - 1.0) < 0.01
    assert result.transition_adjustment == 0.70


def test_regime_weight_integration_applies_performance_tilt() -> None:
    result = RegimeWeightIntegration().integrate("RANGE", "TREND", "NORMAL", {"TREND": 0.20})
    assert result.status == "REGIME_WEIGHT_INTEGRATION_READY"
    assert result.current_regime == "TREND"
    assert result.weights["TREND"] >= result.weights["MOMENTUM"]


def test_milestone_b_regime_runtime_resolves_capital_preservation() -> None:
    result = ProductionMilestoneBRegimeRuntime().run("TREND", "NEWS", "EXTREME", {})
    assert result.status == "MILESTONE_B_REGIME_RUNTIME_READY"
    assert result.execution_mode == "CAPITAL_PRESERVATION"
    assert result.dominant_category in {"RISK", "EXECUTION"}


def test_milestone_b_regime_runtime_supports_backward_defaults() -> None:
    result = ProductionMilestoneBRegimeRuntime().run()
    assert result.status == "MILESTONE_B_REGIME_RUNTIME_READY"
    assert result.current_regime == "BALANCED"
    assert result.weights
