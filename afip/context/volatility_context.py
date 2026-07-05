"""Volatility context assessment for AFIP runtime decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class VolatilityContextResult:
    """Volatility assessment result."""

    status: str
    volatility_state: str
    confidence: float
    adjustment_factor: float
    reason: str


class VolatilityContext:
    """Classifies volatility as low, normal, high, or extreme."""

    def assess(self, metrics: Mapping[str, Any] | None = None) -> VolatilityContextResult:
        data = dict(metrics or {})
        volatility = self._as_score(data.get("volatility", data.get("atr_percentile", 0.50)))

        if volatility >= 0.85:
            state = "EXTREME_VOLATILITY"
            factor = 0.70
            status = "VOLATILITY_REVIEW"
        elif volatility >= 0.65:
            state = "HIGH_VOLATILITY"
            factor = 0.85
            status = "VOLATILITY_READY"
        elif volatility <= 0.25:
            state = "LOW_VOLATILITY"
            factor = 0.90
            status = "VOLATILITY_READY"
        else:
            state = "NORMAL_VOLATILITY"
            factor = 1.00
            status = "VOLATILITY_READY"

        confidence = round(min(100.0, max(0.0, volatility * 100.0)), 2)
        return VolatilityContextResult(
            status=status,
            volatility_state=state,
            confidence=confidence,
            adjustment_factor=factor,
            reason=f"volatility_context_{state.lower()}",
        )

    @staticmethod
    def _as_score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.50
        if score > 1.0:
            score = score / 100.0
        return min(1.0, max(0.0, score))
