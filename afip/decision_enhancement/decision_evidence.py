"""Decision evidence models for regime-first decision intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _direction(value: str) -> str:
    normalized = str(value or "FLAT").strip().upper()
    if normalized in {"BUY", "LONG", "BULLISH"}:
        return "BUY"
    if normalized in {"SELL", "SHORT", "BEARISH"}:
        return "SELL"
    return "FLAT"


@dataclass(frozen=True)
class DecisionEvidence:
    market_regime: str
    volatility_bucket: str
    direction: str
    source: str
    confidence: float
    expectancy: float
    execution_cost_points: float
    reliability: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_regime", str(self.market_regime or "UNKNOWN").strip().upper())
        object.__setattr__(self, "volatility_bucket", str(self.volatility_bucket or "UNKNOWN").strip().upper())
        object.__setattr__(self, "direction", _direction(self.direction))
        object.__setattr__(self, "source", str(self.source or "unknown_source").strip())
        object.__setattr__(self, "confidence", round(max(0.0, min(100.0, float(self.confidence))), 4))
        object.__setattr__(self, "expectancy", round(float(self.expectancy), 4))
        object.__setattr__(self, "execution_cost_points", round(max(0.0, float(self.execution_cost_points)), 4))
        object.__setattr__(self, "reliability", round(max(0.0, min(100.0, float(self.reliability))), 4))

    @property
    def regime_first_key(self) -> str:
        return f"{self.market_regime}|{self.volatility_bucket}|{self.direction}"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DecisionEvidence":
        return cls(
            market_regime=str(value.get("market_regime", "UNKNOWN")),
            volatility_bucket=str(value.get("volatility_bucket", "UNKNOWN")),
            direction=str(value.get("direction", value.get("direction_bias", "FLAT"))),
            source=str(value.get("source", value.get("name", "unknown_source"))),
            confidence=float(value.get("confidence", 0.0)),
            expectancy=float(value.get("expectancy", value.get("expected_value", 0.0))),
            execution_cost_points=float(value.get("execution_cost_points", value.get("average_execution_cost_points", 0.0))),
            reliability=float(value.get("reliability", value.get("quality", 0.0))),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction": self.direction,
            "source": self.source,
            "confidence": self.confidence,
            "expectancy": self.expectancy,
            "execution_cost_points": self.execution_cost_points,
            "reliability": self.reliability,
            "regime_first_key": self.regime_first_key,
        }
