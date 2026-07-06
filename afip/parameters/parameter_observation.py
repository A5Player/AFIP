"""Production Milestone C Pack 13 adaptive parameter observation model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _upper(value: str | None, default: str) -> str:
    text = (value or default).strip().upper()
    return text or default


def _non_negative(value: float | int | None) -> float:
    return max(0.0, float(value or 0.0))


@dataclass(frozen=True)
class ParameterObservation:
    """Observed market outcome used to learn bounded financial parameters."""

    observed_at: datetime
    symbol: str = "GOLD#"
    position_direction: str = "BUY"
    market_regime: str = "BALANCED"
    volatility_bucket: str = "NORMAL"
    session: str = "GLOBAL"
    entry_quality: float = 70.0
    result_amount: float = 0.0
    stop_distance_points: float = 0.0
    favorable_excursion_points: float = 0.0
    adverse_excursion_points: float = 0.0
    holding_minutes: float = 0.0
    execution_cost_points: float = 0.0
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        timestamp = self.observed_at
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        object.__setattr__(self, "observed_at", timestamp)
        object.__setattr__(self, "symbol", _upper(self.symbol, "GOLD#"))
        object.__setattr__(self, "position_direction", _upper(self.position_direction, "BUY"))
        object.__setattr__(self, "market_regime", _upper(self.market_regime, "BALANCED"))
        object.__setattr__(self, "volatility_bucket", _upper(self.volatility_bucket, "NORMAL"))
        object.__setattr__(self, "session", _upper(self.session, "GLOBAL"))
        object.__setattr__(self, "entry_quality", max(0.0, min(100.0, float(self.entry_quality))))
        object.__setattr__(self, "result_amount", float(self.result_amount))
        object.__setattr__(self, "stop_distance_points", _non_negative(self.stop_distance_points))
        object.__setattr__(self, "favorable_excursion_points", _non_negative(self.favorable_excursion_points))
        object.__setattr__(self, "adverse_excursion_points", _non_negative(self.adverse_excursion_points))
        object.__setattr__(self, "holding_minutes", _non_negative(self.holding_minutes))
        object.__setattr__(self, "execution_cost_points", _non_negative(self.execution_cost_points))
        object.__setattr__(self, "tags", tuple(_upper(tag, "TAG") for tag in self.tags if str(tag).strip()))

    @property
    def parameter_key(self) -> str:
        """Stable grouping key for regime-first parameter learning."""
        return "|".join((self.symbol, self.market_regime, self.volatility_bucket, self.position_direction))

    @property
    def won(self) -> bool:
        return self.result_amount > 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "observed_at": self.observed_at.isoformat(),
            "symbol": self.symbol,
            "position_direction": self.position_direction,
            "market_regime": self.market_regime,
            "volatility_bucket": self.volatility_bucket,
            "session": self.session,
            "entry_quality": round(self.entry_quality, 4),
            "result_amount": round(self.result_amount, 4),
            "stop_distance_points": round(self.stop_distance_points, 4),
            "favorable_excursion_points": round(self.favorable_excursion_points, 4),
            "adverse_excursion_points": round(self.adverse_excursion_points, 4),
            "holding_minutes": round(self.holding_minutes, 4),
            "execution_cost_points": round(self.execution_cost_points, 4),
            "parameter_key": self.parameter_key,
            "tags": list(self.tags),
        }
