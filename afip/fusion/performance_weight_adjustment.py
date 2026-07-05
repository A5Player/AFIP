"""Performance-based weight adjustment for AFIP intelligence fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PerformanceWeightAdjustmentResult:
    """Adjusted weights after performance attribution."""

    status: str
    weights: dict[str, float]
    positive_adjustments: int
    negative_adjustments: int
    reason: str


class PerformanceWeightAdjustment:
    """Adjust allocation weights using realized performance attribution."""

    def adjust(
        self,
        base_weights: Mapping[str, float],
        performance_attribution: Mapping[str, float],
    ) -> PerformanceWeightAdjustmentResult:
        if not base_weights:
            return PerformanceWeightAdjustmentResult("PERFORMANCE_WEIGHT_REVIEW", {}, 0, 0, "missing_base_weights")

        adjusted: dict[str, float] = {}
        positive = 0
        negative = 0
        for category, weight in base_weights.items():
            performance = float(performance_attribution.get(category, 0.0))
            multiplier = 1.0 + max(-0.25, min(0.25, performance))
            if performance > 0:
                positive += 1
            elif performance < 0:
                negative += 1
            adjusted[str(category).upper()] = max(0.01, float(weight) * multiplier)

        total = sum(adjusted.values())
        normalized = {category: round(value / total, 4) for category, value in adjusted.items()}
        return PerformanceWeightAdjustmentResult(
            status="PERFORMANCE_WEIGHT_READY",
            weights=normalized,
            positive_adjustments=positive,
            negative_adjustments=negative,
            reason="performance_attribution_weight_adjustment",
        )
