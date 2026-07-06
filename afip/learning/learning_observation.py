"""Regime-first learning observation primitives for Milestone C Pack 15.

Learning observations are derived from completed financial outcomes.  They keep
market regime ahead of signal details so adaptive learning cannot bypass market
context or introduce non-deterministic runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Any


def _normalize(value: str | None, default: str = "UNKNOWN") -> str:
    text = (value or default).strip().replace(" ", "_").replace("-", "_").upper()
    return text or default


@dataclass(frozen=True)
class LearningObservation:
    """Single closed-outcome learning observation with regime-first identity."""

    observed_at: datetime
    market_regime: str = "UNKNOWN"
    volatility_bucket: str = "UNKNOWN"
    direction: str = "FLAT"
    signal_family: str = "UNSPECIFIED"
    confidence: float = 0.0
    result_amount: float = 0.0
    execution_cost_points: float = 0.0
    capital_risk_amount: float = 0.0
    source: str = "RESEARCH_PLATFORM"

    def __post_init__(self) -> None:
        observed_at = self.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        object.__setattr__(self, "observed_at", observed_at.astimezone(timezone.utc))
        object.__setattr__(self, "market_regime", _normalize(self.market_regime))
        object.__setattr__(self, "volatility_bucket", _normalize(self.volatility_bucket))
        object.__setattr__(self, "direction", _normalize(self.direction, "FLAT"))
        object.__setattr__(self, "signal_family", _normalize(self.signal_family, "UNSPECIFIED"))
        object.__setattr__(self, "source", _normalize(self.source, "RESEARCH_PLATFORM"))
        object.__setattr__(self, "confidence", float(self.confidence))
        object.__setattr__(self, "result_amount", float(self.result_amount))
        object.__setattr__(self, "execution_cost_points", float(self.execution_cost_points))
        object.__setattr__(self, "capital_risk_amount", float(self.capital_risk_amount))

    @property
    def regime_first_key(self) -> str:
        return "|".join((self.market_regime, self.volatility_bucket, self.direction, self.signal_family))

    @property
    def net_learning_amount(self) -> float:
        return round(self.result_amount - self.execution_cost_points, 4)

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction": self.direction,
            "signal_family": self.signal_family,
            "confidence": self.confidence,
            "result_amount": self.result_amount,
            "execution_cost_points": self.execution_cost_points,
            "capital_risk_amount": self.capital_risk_amount,
            "source": self.source,
            "regime_first_key": self.regime_first_key,
            "net_learning_amount": self.net_learning_amount,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "LearningObservation":
        raw_time = payload.get("observed_at")
        if isinstance(raw_time, datetime):
            observed_at = raw_time
        elif isinstance(raw_time, str) and raw_time:
            observed_at = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        else:
            observed_at = datetime(1970, 1, 1, tzinfo=timezone.utc)
        return cls(
            observed_at=observed_at,
            market_regime=str(payload.get("market_regime", "UNKNOWN")),
            volatility_bucket=str(payload.get("volatility_bucket", "UNKNOWN")),
            direction=str(payload.get("direction", "FLAT")),
            signal_family=str(payload.get("signal_family", "UNSPECIFIED")),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
            result_amount=float(payload.get("result_amount", 0.0) or 0.0),
            execution_cost_points=float(payload.get("execution_cost_points", 0.0) or 0.0),
            capital_risk_amount=float(payload.get("capital_risk_amount", 0.0) or 0.0),
            source=str(payload.get("source", "RESEARCH_PLATFORM")),
        )
