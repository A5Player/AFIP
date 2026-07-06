"""Market regime classifier that runs before signal evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any

from .regime_thresholds import RegimeThresholds


@dataclass(frozen=True)
class RegimeClassification:
    status: str
    market_regime: str
    volatility_bucket: str
    direction_bias: str
    confidence: float
    reasons: list[str]
    thresholds: dict[str, object]

    @property
    def regime_first_key(self) -> str:
        return f"{self.market_regime}|{self.volatility_bucket}|{self.direction_bias}"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction_bias": self.direction_bias,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "thresholds": dict(self.thresholds),
            "regime_first_key": self.regime_first_key,
        }


class RegimeClassifier:
    """Classify the current market state using learned thresholds only."""

    def classify(self, snapshot: Mapping[str, Any], thresholds: RegimeThresholds | None) -> RegimeClassification:
        if thresholds is None:
            return RegimeClassification(
                status="REGIME_DATA_REQUIRED",
                market_regime="UNKNOWN",
                volatility_bucket="UNKNOWN",
                direction_bias="FLAT",
                confidence=0.0,
                reasons=["learned_regime_thresholds_required"],
                thresholds={},
            )

        range_percent = float(snapshot.get("range_percent", 0.0))
        trend_efficiency = float(snapshot.get("trend_efficiency", 0.0))
        participation_score = float(snapshot.get("participation_score", 0.0))
        transition_pressure = float(snapshot.get("transition_pressure", 0.0))
        directional_pressure = float(snapshot.get("directional_pressure", 0.0))

        if range_percent >= thresholds.expansion_range_percent:
            market_regime = "EXPANSION"
        elif range_percent <= thresholds.quiet_range_percent:
            market_regime = "QUIET"
        else:
            market_regime = "NORMAL"

        volatility_bucket = "HIGH" if range_percent >= thresholds.expansion_range_percent else "NORMAL"
        if range_percent <= thresholds.quiet_range_percent:
            volatility_bucket = "LOW"

        if directional_pressure > 0:
            direction_bias = "BUY"
        elif directional_pressure < 0:
            direction_bias = "SELL"
        else:
            direction_bias = "FLAT"

        reasons: list[str] = ["market_regime_classified_before_signal"]
        quality_components = []
        if trend_efficiency >= thresholds.trend_efficiency_floor:
            quality_components.append(30.0)
            reasons.append("trend_efficiency_above_learned_floor")
        if participation_score >= thresholds.participation_floor:
            quality_components.append(30.0)
            reasons.append("participation_above_learned_floor")
        if abs(transition_pressure) <= thresholds.transition_pressure_ceiling:
            quality_components.append(20.0)
            reasons.append("transition_pressure_within_learned_ceiling")
        if market_regime != "UNKNOWN":
            quality_components.append(20.0)
        confidence = round(sum(quality_components), 4)
        return RegimeClassification(
            status="REGIME_CLASSIFICATION_READY",
            market_regime=market_regime,
            volatility_bucket=volatility_bucket,
            direction_bias=direction_bias,
            confidence=confidence,
            reasons=reasons,
            thresholds=thresholds.as_dict(),
        )
