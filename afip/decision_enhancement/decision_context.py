"""Build deterministic decision context after market regime classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class DecisionContext:
    status: str
    market_regime: str
    volatility_bucket: str
    direction_bias: str
    regime_confidence: float
    reasons: tuple[str, ...]

    @property
    def regime_first_key(self) -> str:
        return f"{self.market_regime}|{self.volatility_bucket}|{self.direction_bias}"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction_bias": self.direction_bias,
            "regime_confidence": self.regime_confidence,
            "reasons": list(self.reasons),
            "regime_first_key": self.regime_first_key,
        }


class DecisionContextBuilder:
    """Require market regime state before decision evidence is evaluated."""

    def build(self, regime_classification: Mapping[str, Any] | None) -> DecisionContext:
        if not regime_classification or regime_classification.get("status") != "REGIME_CLASSIFICATION_READY":
            return DecisionContext(
                status="DECISION_CONTEXT_DATA_REQUIRED",
                market_regime="UNKNOWN",
                volatility_bucket="UNKNOWN",
                direction_bias="FLAT",
                regime_confidence=0.0,
                reasons=("market_regime_classification_required_before_decision",),
            )
        return DecisionContext(
            status="DECISION_CONTEXT_READY",
            market_regime=str(regime_classification.get("market_regime", "UNKNOWN")).upper(),
            volatility_bucket=str(regime_classification.get("volatility_bucket", "UNKNOWN")).upper(),
            direction_bias=str(regime_classification.get("direction_bias", "FLAT")).upper(),
            regime_confidence=round(float(regime_classification.get("confidence", 0.0)), 4),
            reasons=("market_regime_context_accepted_before_signal",),
        )
