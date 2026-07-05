"""Production Milestone A2: Market Regime Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from afip.intelligence.adaptive_intelligence_core import clamp


@dataclass(frozen=True)
class MarketRegimeResult:
    status: str
    regime: str
    confidence: float
    action_bias: str
    risk_adjustment: float
    entry_threshold_adjustment: float
    reason: str
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "regime": self.regime,
            "confidence": round(self.confidence, 2),
            "action_bias": self.action_bias,
            "risk_adjustment": round(self.risk_adjustment, 2),
            "entry_threshold_adjustment": round(self.entry_threshold_adjustment, 2),
            "reason": self.reason,
            "diagnostics": dict(self.diagnostics),
        }


class MarketRegimeIntelligenceV2:
    """Classifies financial market conditions into production-safe regimes."""

    def classify(self, features: Mapping[str, Any]) -> MarketRegimeResult:
        trend = clamp(float(features.get("trend_strength", 50.0)))
        volatility = clamp(float(features.get("volatility_score", features.get("atr_percentile", 50.0))))
        liquidity = clamp(float(features.get("liquidity_score", 70.0)))
        spread_quality = clamp(float(features.get("spread_quality", 70.0)))
        structure = clamp(float(features.get("structure_quality", 50.0)))

        if liquidity < 35.0 or spread_quality < 35.0:
            return MarketRegimeResult("READY", "LOW_LIQUIDITY", max(70.0, 100.0 - min(liquidity, spread_quality)), "HOLD", -25.0, 12.0, "liquidity_or_spread_quality_low", dict(features))
        if volatility >= 78.0 and trend < 62.0:
            return MarketRegimeResult("READY", "VOLATILE", volatility, "HOLD", -18.0, 10.0, "volatility_high_without_trend_alignment", dict(features))
        if trend >= 68.0 and structure >= 58.0 and volatility <= 82.0:
            confidence = (trend * 0.55) + (structure * 0.30) + ((100.0 - abs(volatility - 55.0)) * 0.15)
            return MarketRegimeResult("READY", "TRENDING", clamp(confidence), "FOLLOW_TREND", 8.0, -4.0, "trend_and_structure_aligned", dict(features))
        if trend <= 42.0 and volatility <= 62.0:
            confidence = (100.0 - trend) * 0.60 + (100.0 - volatility) * 0.20 + liquidity * 0.20
            return MarketRegimeResult("READY", "RANGING", clamp(confidence), "MEAN_REVERSION", -5.0, 4.0, "trend_low_and_volatility_contained", dict(features))
        return MarketRegimeResult("READY", "TRANSITION", 60.0, "HOLD", -10.0, 8.0, "market_transition_requires_confirmation", dict(features))
