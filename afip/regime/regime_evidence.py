"""Market regime evidence records for Production Milestone C Pack 16."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class RegimeEvidence:
    """Normalized evidence used before any directional signal is considered."""

    observed_at: datetime
    market_regime: str
    volatility_bucket: str
    direction: str
    range_percent: float
    trend_efficiency: float
    participation_score: float
    transition_pressure: float
    result_amount: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_regime", self._normalize_label(self.market_regime))
        object.__setattr__(self, "volatility_bucket", self._normalize_label(self.volatility_bucket))
        object.__setattr__(self, "direction", self._normalize_direction(self.direction))
        object.__setattr__(self, "range_percent", round(float(self.range_percent), 6))
        object.__setattr__(self, "trend_efficiency", round(float(self.trend_efficiency), 6))
        object.__setattr__(self, "participation_score", round(float(self.participation_score), 6))
        object.__setattr__(self, "transition_pressure", round(float(self.transition_pressure), 6))
        object.__setattr__(self, "result_amount", round(float(self.result_amount), 6))

    @property
    def regime_first_key(self) -> str:
        return f"{self.market_regime}|{self.volatility_bucket}|{self.direction}"

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "direction": self.direction,
            "range_percent": self.range_percent,
            "trend_efficiency": self.trend_efficiency,
            "participation_score": self.participation_score,
            "transition_pressure": self.transition_pressure,
            "result_amount": self.result_amount,
            "regime_first_key": self.regime_first_key,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RegimeEvidence":
        observed_at = payload.get("observed_at")
        if isinstance(observed_at, str):
            observed_at = datetime.fromisoformat(observed_at)
        if not isinstance(observed_at, datetime):
            raise ValueError("observed_at must be datetime or ISO datetime string")
        return cls(
            observed_at=observed_at,
            market_regime=str(payload.get("market_regime", "unknown")),
            volatility_bucket=str(payload.get("volatility_bucket", "unknown")),
            direction=str(payload.get("direction", "flat")),
            range_percent=float(payload.get("range_percent", 0.0)),
            trend_efficiency=float(payload.get("trend_efficiency", 0.0)),
            participation_score=float(payload.get("participation_score", 0.0)),
            transition_pressure=float(payload.get("transition_pressure", 0.0)),
            result_amount=float(payload.get("result_amount", 0.0)),
        )

    @staticmethod
    def _normalize_label(value: object) -> str:
        text = str(value).strip().upper().replace(" ", "_").replace("-", "_")
        return text or "UNKNOWN"

    @staticmethod
    def _normalize_direction(value: object) -> str:
        text = str(value).strip().upper()
        if text in {"BUY", "BULL", "BULLISH", "LONG"}:
            return "BUY"
        if text in {"SELL", "BEAR", "BEARISH", "SHORT"}:
            return "SELL"
        return "FLAT"
