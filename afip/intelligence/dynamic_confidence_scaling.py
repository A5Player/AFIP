"""Dynamic confidence scaling for AFIP Production Milestone A Pack 11."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class ConfidenceScalingResult:
    """Scaled confidence output for production decision layers."""

    raw_confidence: float
    scaled_confidence: float
    scaling_factor: float
    confidence_band: str
    reason: str


class DynamicConfidenceScaling:
    """Scale confidence using signal agreement, liquidity, and execution quality."""

    def scale(
        self,
        raw_confidence: float,
        signal_values: Iterable[float],
        liquidity_quality: float,
        execution_quality: float,
    ) -> ConfidenceScalingResult:
        """Return production confidence adjusted for quality and consistency."""
        raw = _bounded(raw_confidence, 0.0, 100.0)
        values = [_bounded(value, 0.0, 100.0) for value in signal_values]
        if not values:
            values = [raw]

        mean_signal = sum(values) / len(values)
        dispersion = sum(abs(value - mean_signal) for value in values) / len(values)
        consistency = _bounded(1.0 - dispersion / 100.0, 0.0, 1.0)
        liquidity = _bounded(liquidity_quality, 0.0, 1.0)
        execution = _bounded(execution_quality, 0.0, 1.0)

        scaling_factor = _bounded(0.55 + consistency * 0.20 + liquidity * 0.15 + execution * 0.15, 0.45, 1.10)
        scaled = _bounded(raw * scaling_factor, 0.0, 100.0)

        if scaled >= 78.0:
            confidence_band = "HIGH_CONFIDENCE"
            reason = "scaled_confidence_supports_production_decision"
        elif scaled >= 62.0:
            confidence_band = "MODERATE_CONFIDENCE"
            reason = "scaled_confidence_requires_standard_allocation"
        else:
            confidence_band = "LOW_CONFIDENCE"
            reason = "scaled_confidence_requires_reduced_allocation"

        return ConfidenceScalingResult(
            raw_confidence=round(raw, 4),
            scaled_confidence=round(scaled, 4),
            scaling_factor=round(scaling_factor, 4),
            confidence_band=confidence_band,
            reason=reason,
        )
