"""Optimization runtime for AFIP Production Milestone A Pack 11."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.intelligence.adaptive_parameter_calibration import AdaptiveParameterCalibration, ParameterCalibrationResult
from afip.intelligence.dynamic_confidence_scaling import ConfidenceScalingResult, DynamicConfidenceScaling
from afip.learning.learning_quality_evaluation import LearningQualityEvaluation, LearningQualityResult


@dataclass(frozen=True)
class OptimizationRuntimeResult:
    """Integrated output from the Pack 11 optimization runtime."""

    status: str
    action: str
    calibrated_parameters: ParameterCalibrationResult
    confidence_scaling: ConfidenceScalingResult
    learning_quality: LearningQualityResult
    reason: str


class ProductionMilestoneAOptimizationRuntime:
    """Integrate adaptive calibration, confidence scaling, and learning quality."""

    def __init__(self) -> None:
        self._calibration = AdaptiveParameterCalibration()
        self._scaling = DynamicConfidenceScaling()
        self._learning = LearningQualityEvaluation()

    def evaluate(
        self,
        market_metrics: Mapping[str, float],
        learning_metrics: Mapping[str, float],
        raw_confidence: float,
        signal_values: Iterable[float],
    ) -> OptimizationRuntimeResult:
        """Return an optimization decision that is safe for simulation and CI."""
        learning_quality = self._learning.evaluate(learning_metrics)
        merged_metrics = dict(market_metrics)
        merged_metrics["learning_quality"] = learning_quality.quality_score

        calibrated_parameters = self._calibration.calibrate(merged_metrics)
        confidence_scaling = self._scaling.scale(
            raw_confidence=raw_confidence,
            signal_values=signal_values,
            liquidity_quality=float(market_metrics.get("liquidity_quality", 0.50)),
            execution_quality=float(market_metrics.get("execution_quality", 0.50)),
        )

        confidence_ratio = confidence_scaling.scaled_confidence / 100.0
        if learning_quality.status == "OBSERVATION_ONLY":
            status = "OBSERVATION_ONLY"
            action = "NO_PARAMETER_CHANGE"
            reason = "learning_quality_not_ready_for_optimization"
        elif confidence_ratio >= calibrated_parameters.entry_threshold:
            status = "OPTIMIZATION_APPROVED"
            action = "APPLY_CALIBRATED_PARAMETERS"
            reason = "scaled_confidence_exceeds_calibrated_entry_threshold"
        elif confidence_ratio <= calibrated_parameters.exit_threshold:
            status = "OPTIMIZATION_REDUCED"
            action = "REDUCE_ALLOCATION_PARAMETERS"
            reason = "scaled_confidence_below_calibrated_exit_threshold"
        else:
            status = "OPTIMIZATION_STABLE"
            action = "MAINTAIN_CURRENT_PARAMETERS"
            reason = "scaled_confidence_inside_calibrated_operating_range"

        return OptimizationRuntimeResult(
            status=status,
            action=action,
            calibrated_parameters=calibrated_parameters,
            confidence_scaling=confidence_scaling,
            learning_quality=learning_quality,
            reason=reason,
        )
