"""Liquidity context assessment for AFIP market decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LiquidityContextResult:
    """Liquidity context output."""

    status: str
    liquidity_state: str
    confidence: float
    execution_quality_factor: float
    reason: str


class LiquidityContext:
    """Classifies liquidity expansion or contraction for execution planning."""

    def assess(self, metrics: Mapping[str, Any] | None = None) -> LiquidityContextResult:
        data = dict(metrics or {})
        liquidity_depth = self._as_score(data.get("liquidity_depth", 0.50))
        spread_quality = self._as_score(data.get("spread_quality", 0.50))
        volume_participation = self._as_score(data.get("volume_participation", 0.50))
        composite = (liquidity_depth * 0.40) + (spread_quality * 0.35) + (volume_participation * 0.25)

        if composite >= 0.70:
            state = "LIQUIDITY_EXPANSION"
            factor = 1.05
            status = "LIQUIDITY_READY"
        elif composite <= 0.35:
            state = "LIQUIDITY_CONTRACTION"
            factor = 0.75
            status = "LIQUIDITY_REVIEW"
        else:
            state = "BALANCED_LIQUIDITY"
            factor = 1.00
            status = "LIQUIDITY_READY"

        confidence = round(composite * 100.0, 2)
        return LiquidityContextResult(
            status=status,
            liquidity_state=state,
            confidence=confidence,
            execution_quality_factor=factor,
            reason=f"liquidity_context_{state.lower()}",
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
