"""Historical market observation schema for compact long-term analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class HistoricalMarketObservation:
    """Normalized historical observation captured at an important market stage."""

    observed_at: datetime
    symbol: str
    timeframe: str
    session: str
    market_regime: str
    direction: str
    confidence: float
    close_price: float
    spread_points: float = 0.0
    volatility_points: float = 0.0
    macro_bias: str = "NEUTRAL"
    institutional_bias: str = "NEUTRAL"
    signature_id: str = "UNKNOWN_SIGNATURE"
    stage: str = "OBSERVATION"
    source: str = "INTERNAL"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.observed_at
        if normalized.tzinfo is None:
            normalized = normalized.replace(tzinfo=timezone.utc)
        else:
            normalized = normalized.astimezone(timezone.utc)
        object.__setattr__(self, "observed_at", normalized)
        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "timeframe", self.timeframe.upper())
        object.__setattr__(self, "session", self.session.upper())
        object.__setattr__(self, "market_regime", self.market_regime.upper())
        object.__setattr__(self, "direction", self.direction.upper())
        object.__setattr__(self, "macro_bias", self.macro_bias.upper())
        object.__setattr__(self, "institutional_bias", self.institutional_bias.upper())
        object.__setattr__(self, "stage", self.stage.upper())
        object.__setattr__(self, "source", self.source.upper())

    @property
    def day_key(self) -> str:
        return self.observed_at.date().isoformat()

    @property
    def session_key(self) -> str:
        return f"{self.day_key}:{self.session}"

    def compact_key(self) -> str:
        return "|".join(
            [
                self.symbol,
                self.timeframe,
                self.session,
                self.market_regime,
                self.direction,
                self.macro_bias,
                self.institutional_bias,
                self.signature_id,
            ]
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "session": self.session,
            "market_regime": self.market_regime,
            "direction": self.direction,
            "confidence": round(float(self.confidence), 4),
            "close_price": round(float(self.close_price), 5),
            "spread_points": round(float(self.spread_points), 4),
            "volatility_points": round(float(self.volatility_points), 4),
            "macro_bias": self.macro_bias,
            "institutional_bias": self.institutional_bias,
            "signature_id": self.signature_id,
            "stage": self.stage,
            "source": self.source,
            "metadata": dict(self.metadata),
        }
