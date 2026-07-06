"""Normalized financial data records for Production Milestone D Pack 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _text(value: object, default: str = "UNKNOWN") -> str:
    text = str(value or default).strip().upper()
    return text or default


def _float(value: object) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        number = 0.0
    return round(number, 6)


def _ratio(value: object) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        number = 0.0
    return round(max(0.0, min(1.0, number)), 6)


@dataclass(frozen=True)
class FinancialDataRecord:
    """A deterministic input record that enters the runtime data pipeline."""

    source_key: str
    market_regime: str
    timeframe: str
    sequence_index: int
    close_price: float
    spread_points: float
    liquidity_score: float
    completeness_ratio: float
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_key", _text(self.source_key))
        object.__setattr__(self, "market_regime", _text(self.market_regime))
        object.__setattr__(self, "timeframe", _text(self.timeframe))
        object.__setattr__(self, "sequence_index", max(0, int(self.sequence_index)))
        object.__setattr__(self, "close_price", max(0.0, _float(self.close_price)))
        object.__setattr__(self, "spread_points", max(0.0, _float(self.spread_points)))
        object.__setattr__(self, "liquidity_score", max(0.0, min(100.0, _float(self.liquidity_score))))
        object.__setattr__(self, "completeness_ratio", _ratio(self.completeness_ratio))
        object.__setattr__(self, "reason", str(self.reason or "financial_data_observed"))

    @property
    def is_usable(self) -> bool:
        return self.close_price > 0.0 and self.completeness_ratio >= 0.5 and self.liquidity_score > 0.0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], sequence_index: int = 0) -> "FinancialDataRecord":
        return cls(
            source_key=str(payload.get("source_key", payload.get("source", "UNKNOWN"))),
            market_regime=str(payload.get("market_regime", payload.get("regime", "UNKNOWN"))),
            timeframe=str(payload.get("timeframe", payload.get("tf", "UNKNOWN"))),
            sequence_index=int(payload.get("sequence_index", sequence_index) or sequence_index),
            close_price=payload.get("close_price", payload.get("close", 0.0)),
            spread_points=payload.get("spread_points", payload.get("spread", 0.0)),
            liquidity_score=payload.get("liquidity_score", payload.get("liquidity", 0.0)),
            completeness_ratio=payload.get("completeness_ratio", payload.get("completeness", 0.0)),
            reason=str(payload.get("reason", "financial_data_observed")),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "source_key": self.source_key,
            "market_regime": self.market_regime,
            "timeframe": self.timeframe,
            "sequence_index": self.sequence_index,
            "close_price": self.close_price,
            "spread_points": self.spread_points,
            "liquidity_score": self.liquidity_score,
            "completeness_ratio": self.completeness_ratio,
            "reason": self.reason,
            "is_usable": self.is_usable,
        }
