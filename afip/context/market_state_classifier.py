"""Market state classification for AFIP decision context.

This module is additive and keeps existing runtime behaviour unchanged.
It converts normalized market metrics into a production-safe market state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class MarketStateResult:
    """Normalized market state output."""

    status: str
    market_state: str
    confidence: float
    context_score: float
    reason: str


class MarketStateClassifier:
    """Classifies current market state from normalized market metrics."""

    VALID_STATES = {
        "TRENDING",
        "SIDEWAYS",
        "BREAKOUT",
        "PULLBACK",
        "NEUTRAL",
    }

    def classify(self, metrics: Mapping[str, Any] | None = None) -> MarketStateResult:
        """Return a market state using conservative deterministic thresholds."""

        data = dict(metrics or {})
        trend_strength = self._as_score(data.get("trend_strength", 0.0))
        range_balance = self._as_score(data.get("range_balance", 0.0))
        breakout_pressure = self._as_score(data.get("breakout_pressure", 0.0))
        pullback_depth = self._as_score(data.get("pullback_depth", 0.0))

        candidates = {
            "TRENDING": trend_strength,
            "SIDEWAYS": range_balance,
            "BREAKOUT": breakout_pressure,
            "PULLBACK": pullback_depth,
            "NEUTRAL": 0.50,
        }
        market_state = max(candidates, key=candidates.get)
        raw_score = candidates[market_state]
        confidence = round(min(100.0, max(0.0, raw_score * 100.0)), 2)

        status = "MARKET_STATE_READY" if confidence >= 55.0 else "MARKET_STATE_REVIEW"
        reason = f"market_state_{market_state.lower()}"
        return MarketStateResult(
            status=status,
            market_state=market_state,
            confidence=confidence,
            context_score=confidence,
            reason=reason,
        )

    @staticmethod
    def _as_score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        if score > 1.0:
            score = score / 100.0
        return min(1.0, max(0.0, score))
