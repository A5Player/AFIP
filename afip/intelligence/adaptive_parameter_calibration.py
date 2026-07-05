"""Adaptive parameter calibration for AFIP Production Milestone A Pack 11.

The module provides deterministic calibration for production decision parameters.
It uses only financial terminology and remains independent from live execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _bounded(value: float, lower: float, upper: float) -> float:
    """Return a numeric value inside an inclusive range."""
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class ParameterCalibrationResult:
    """Result returned by adaptive parameter calibration."""

    entry_threshold: float
    exit_threshold: float
    allocation_multiplier: float
    confidence_floor: float
    status: str
    reason: str


class AdaptiveParameterCalibration:
    """Calibrate entry, exit, and allocation parameters from market metrics."""

    def calibrate(self, metrics: Mapping[str, float]) -> ParameterCalibrationResult:
        """Build a stable parameter set from normalized production metrics."""
        regime_quality = _bounded(metrics.get("regime_quality", 0.50), 0.0, 1.0)
        execution_quality = _bounded(metrics.get("execution_quality", 0.50), 0.0, 1.0)
        learning_quality = _bounded(metrics.get("learning_quality", 0.50), 0.0, 1.0)
        volatility_pressure = _bounded(metrics.get("volatility_pressure", 0.50), 0.0, 1.0)
        drawdown_pressure = _bounded(metrics.get("drawdown_pressure", 0.50), 0.0, 1.0)

        quality_score = (regime_quality + execution_quality + learning_quality) / 3.0
        pressure_score = (volatility_pressure + drawdown_pressure) / 2.0

        entry_threshold = _bounded(0.70 + pressure_score * 0.10 - quality_score * 0.04, 0.62, 0.86)
        exit_threshold = _bounded(0.42 + pressure_score * 0.12 - quality_score * 0.03, 0.34, 0.62)
        allocation_multiplier = _bounded(0.55 + quality_score * 0.70 - pressure_score * 0.35, 0.25, 1.20)
        confidence_floor = _bounded(0.50 + pressure_score * 0.16 - quality_score * 0.05, 0.45, 0.70)

        if quality_score >= 0.72 and pressure_score <= 0.45:
            status = "EXPANSION_ELIGIBLE"
            reason = "quality_score_supports_higher_allocation"
        elif pressure_score >= 0.70:
            status = "CAPITAL_PRESERVATION"
            reason = "market_pressure_requires_lower_allocation"
        else:
            status = "BALANCED_ALLOCATION"
            reason = "calibration_balances_quality_and_pressure"

        return ParameterCalibrationResult(
            entry_threshold=round(entry_threshold, 4),
            exit_threshold=round(exit_threshold, 4),
            allocation_multiplier=round(allocation_multiplier, 4),
            confidence_floor=round(confidence_floor, 4),
            status=status,
            reason=reason,
        )
