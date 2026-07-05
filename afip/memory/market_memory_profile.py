"""Production Milestone B Pack 9 - market memory profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketMemoryProfileResult:
    status: str
    dominant_regime: str
    volatility_state: str
    liquidity_state: str
    profile_score: float
    reason: str


class MarketMemoryProfile:
    """Summarize the latest market state into a stable memory profile."""

    def evaluate(self, payload: Mapping[str, Any] | None) -> MarketMemoryProfileResult:
        data = dict(payload or {})
        regime = str(data.get("market_regime", data.get("regime", "NEUTRAL"))).upper()
        volatility = str(data.get("volatility_state", data.get("volatility", "NORMAL"))).upper()
        liquidity = str(data.get("liquidity_state", data.get("liquidity", "NORMAL"))).upper()
        confidence = _score(data.get("confidence", data.get("context_score", 50.0)))
        profile_score = _market_profile_score(regime, volatility, liquidity, confidence)
        status = "MARKET_MEMORY_READY" if profile_score >= 55.0 else "MARKET_MEMORY_REVIEW"
        reason = "market_memory_profile_available" if status == "MARKET_MEMORY_READY" else "market_memory_profile_review"
        return MarketMemoryProfileResult(status, regime, volatility, liquidity, profile_score, reason)


def _score(value: Any) -> float:
    numeric = float(value)
    if numeric <= 1.0:
        numeric *= 100.0
    return min(100.0, max(0.0, numeric))


def _market_profile_score(regime: str, volatility: str, liquidity: str, confidence: float) -> float:
    regime_component = 15.0 if regime in {"TRENDING", "BREAKOUT", "PULLBACK"} else 8.0
    volatility_component = 12.0 if volatility in {"NORMAL", "EXPANDING", "HIGH"} else 6.0
    liquidity_component = 13.0 if liquidity in {"NORMAL", "EXPANDING", "HIGH"} else 6.0
    confidence_component = confidence * 0.60
    return round(min(100.0, regime_component + volatility_component + liquidity_component + confidence_component), 2)
