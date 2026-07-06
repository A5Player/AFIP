"""Replay snapshot schema for deterministic historical market playback."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping

from afip.market_history.historical_market_observation import HistoricalMarketObservation


@dataclass(frozen=True)
class ReplaySnapshot:
    """Single replayable historical market snapshot."""

    observed_at: datetime
    symbol: str
    timeframe: str
    market_regime: str
    direction: str
    close_price: float
    confidence: float = 0.0
    spread_points: float = 0.0
    volatility_points: float = 0.0
    session: str = "UNKNOWN"
    macro_bias: str = "NEUTRAL"
    institutional_bias: str = "NEUTRAL"
    signature_id: str = "UNKNOWN_SIGNATURE"
    source: str = "HISTORICAL_REPLAY"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        observed_at = self.observed_at
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        else:
            observed_at = observed_at.astimezone(timezone.utc)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "timeframe", self.timeframe.upper())
        object.__setattr__(self, "market_regime", self.market_regime.upper())
        object.__setattr__(self, "direction", self.direction.upper())
        object.__setattr__(self, "session", self.session.upper())
        object.__setattr__(self, "macro_bias", self.macro_bias.upper())
        object.__setattr__(self, "institutional_bias", self.institutional_bias.upper())
        object.__setattr__(self, "source", self.source.upper())

    def to_observation(self, stage: str = "REPLAY_STEP") -> HistoricalMarketObservation:
        """Convert the snapshot into a compact historical observation."""
        return HistoricalMarketObservation(
            observed_at=self.observed_at,
            symbol=self.symbol,
            timeframe=self.timeframe,
            session=self.session,
            market_regime=self.market_regime,
            direction=self.direction,
            confidence=self.confidence,
            close_price=self.close_price,
            spread_points=self.spread_points,
            volatility_points=self.volatility_points,
            macro_bias=self.macro_bias,
            institutional_bias=self.institutional_bias,
            signature_id=self.signature_id,
            stage=stage,
            source=self.source,
            metadata=dict(self.metadata),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "market_regime": self.market_regime,
            "direction": self.direction,
            "close_price": round(float(self.close_price), 5),
            "confidence": round(float(self.confidence), 4),
            "spread_points": round(float(self.spread_points), 4),
            "volatility_points": round(float(self.volatility_points), 4),
            "session": self.session,
            "macro_bias": self.macro_bias,
            "institutional_bias": self.institutional_bias,
            "signature_id": self.signature_id,
            "source": self.source,
            "metadata": dict(self.metadata),
        }
