"""Tests for AFIP Production Milestone A Pack 11."""

from afip.intelligence.adaptive_parameter_calibration import AdaptiveParameterCalibration
from afip.intelligence.dynamic_confidence_scaling import DynamicConfidenceScaling
from afip.learning.learning_quality_evaluation import LearningQualityEvaluation
from afip.runtime.production_milestone_a_optimization_runtime import ProductionMilestoneAOptimizationRuntime


def test_parameter_calibration_balances_quality_and_pressure() -> None:
    result = AdaptiveParameterCalibration().calibrate(
        {
            "regime_quality": 0.80,
            "execution_quality": 0.76,
            "learning_quality": 0.74,
            "volatility_pressure": 0.35,
            "drawdown_pressure": 0.30,
        }
    )
    assert 0.62 <= result.entry_threshold <= 0.86
    assert result.allocation_multiplier > 0.70
    assert result.status in {"EXPANSION_ELIGIBLE", "BALANCED_ALLOCATION"}


def test_parameter_calibration_reduces_allocation_under_pressure() -> None:
    result = AdaptiveParameterCalibration().calibrate(
        {
            "regime_quality": 0.40,
            "execution_quality": 0.42,
            "learning_quality": 0.38,
            "volatility_pressure": 0.88,
            "drawdown_pressure": 0.82,
        }
    )
    assert result.status == "CAPITAL_PRESERVATION"
    assert result.allocation_multiplier < 0.60


def test_dynamic_confidence_scaling_returns_high_confidence_band() -> None:
    result = DynamicConfidenceScaling().scale(
        raw_confidence=88.0,
        signal_values=[86.0, 89.0, 91.0],
        liquidity_quality=0.82,
        execution_quality=0.80,
    )
    assert result.scaled_confidence >= 78.0
    assert result.confidence_band == "HIGH_CONFIDENCE"


def test_dynamic_confidence_scaling_handles_empty_signals() -> None:
    result = DynamicConfidenceScaling().scale(
        raw_confidence=55.0,
        signal_values=[],
        liquidity_quality=0.50,
        execution_quality=0.50,
    )
    assert result.raw_confidence == 55.0
    assert 0.0 <= result.scaled_confidence <= 100.0


def test_learning_quality_evaluation_ready_status() -> None:
    result = LearningQualityEvaluation().evaluate(
        {
            "sample_count": 360,
            "win_rate": 0.66,
            "profit_factor": 1.85,
            "drawdown_ratio": 0.18,
            "drift_ratio": 0.12,
        }
    )
    assert result.status == "OPTIMIZATION_READY"
    assert result.quality_score >= 0.72


def test_learning_quality_evaluation_observation_status() -> None:
    result = LearningQualityEvaluation().evaluate(
        {
            "sample_count": 24,
            "win_rate": 0.42,
            "profit_factor": 0.80,
            "drawdown_ratio": 0.62,
            "drift_ratio": 0.55,
        }
    )
    assert result.status == "OBSERVATION_ONLY"
    assert result.quality_score < 0.50


def test_optimization_runtime_approves_calibrated_parameters() -> None:
    result = ProductionMilestoneAOptimizationRuntime().evaluate(
        market_metrics={
            "regime_quality": 0.82,
            "execution_quality": 0.84,
            "liquidity_quality": 0.86,
            "volatility_pressure": 0.28,
            "drawdown_pressure": 0.22,
        },
        learning_metrics={
            "sample_count": 420,
            "win_rate": 0.68,
            "profit_factor": 2.10,
            "drawdown_ratio": 0.12,
            "drift_ratio": 0.10,
        },
        raw_confidence=90.0,
        signal_values=[88.0, 91.0, 89.0],
    )
    assert result.status == "OPTIMIZATION_APPROVED"
    assert result.action == "APPLY_CALIBRATED_PARAMETERS"


def test_optimization_runtime_keeps_backward_safe_observation_mode() -> None:
    result = ProductionMilestoneAOptimizationRuntime().evaluate(
        market_metrics={
            "regime_quality": 0.55,
            "execution_quality": 0.50,
            "liquidity_quality": 0.48,
            "volatility_pressure": 0.45,
            "drawdown_pressure": 0.42,
        },
        learning_metrics={
            "sample_count": 10,
            "win_rate": 0.40,
            "profit_factor": 0.70,
            "drawdown_ratio": 0.70,
            "drift_ratio": 0.65,
        },
        raw_confidence=82.0,
        signal_values=[80.0, 84.0, 83.0],
    )
    assert result.status == "OBSERVATION_ONLY"
    assert result.action == "NO_PARAMETER_CHANGE"
