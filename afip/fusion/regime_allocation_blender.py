from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RegimeAllocationBlendResult:
    status: str
    weights: dict[str, float]
    dominant_category: str
    transition_adjustment: float
    reason: str


class RegimeAllocationBlender:
    """Blend regime and volatility allocation profiles into one normalized profile."""

    def blend(
        self,
        regime_weights: Mapping[str, float],
        volatility_weights: Mapping[str, float],
        transition_risk: float,
    ) -> RegimeAllocationBlendResult:
        if not regime_weights and not volatility_weights:
            return RegimeAllocationBlendResult(
                status="REGIME_ALLOCATION_REVIEW",
                weights={},
                dominant_category="NONE",
                transition_adjustment=0.0,
                reason="insufficient_allocation_inputs",
            )
        transition = min(max(float(transition_risk or 0.0), 0.0), 1.0)
        regime_factor = max(0.35, 0.70 - transition * 0.25)
        volatility_factor = 1.0 - regime_factor
        categories = set(regime_weights) | set(volatility_weights)
        blended = {
            category: float(regime_weights.get(category, 0.0)) * regime_factor
            + float(volatility_weights.get(category, 0.0)) * volatility_factor
            for category in categories
        }
        total = sum(max(value, 0.0) for value in blended.values())
        if total <= 0:
            return RegimeAllocationBlendResult("REGIME_ALLOCATION_REVIEW", {}, "NONE", transition, "zero_allocation_total")
        normalized = {category: round(max(value, 0.0) / total, 4) for category, value in blended.items()}
        dominant = max(normalized, key=normalized.get)
        return RegimeAllocationBlendResult(
            status="REGIME_ALLOCATION_READY",
            weights=normalized,
            dominant_category=dominant,
            transition_adjustment=round(transition, 4),
            reason="regime_volatility_allocation_blended",
        )
