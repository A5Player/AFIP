"""Adaptive AI foundation profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveAIFoundationProfile:
    """Regime-first profile derived from observed market knowledge."""

    market_regime: str
    sample_count: int
    total_weight: float
    weighted_result: float
    win_rate: float
    average_confidence: float
    average_knowledge_quality: float
    adaptive_bias: str

    @property
    def expectancy(self) -> float:
        if self.total_weight == 0.0:
            return 0.0
        return round(self.weighted_result / self.total_weight, 6)

    @property
    def readiness_score(self) -> float:
        if self.sample_count == 0:
            return 0.0
        value = (self.win_rate + self.average_confidence + self.average_knowledge_quality) / 3.0
        return round(value, 6)

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "sample_count": self.sample_count,
            "total_weight": round(self.total_weight, 6),
            "weighted_result": round(self.weighted_result, 6),
            "win_rate": self.win_rate,
            "average_confidence": self.average_confidence,
            "average_knowledge_quality": self.average_knowledge_quality,
            "adaptive_bias": self.adaptive_bias,
            "expectancy": self.expectancy,
            "readiness_score": self.readiness_score,
        }
