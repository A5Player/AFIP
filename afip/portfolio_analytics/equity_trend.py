"""Portfolio equity trend analytics for production review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class EquityTrendResult:
    """Equity trend analytics output."""

    status: str
    ready: bool
    opening_equity: float
    closing_equity: float
    equity_change: float
    trend_direction: str
    trend_strength_percent: float
    reason: str


class EquityTrend:
    """Measure portfolio equity direction and strength from equity observations."""

    def calculate(self, equity_observations: Iterable[Mapping[str, object]] | object) -> EquityTrendResult:
        observations = list(equity_observations or [])
        if len(observations) < 2:
            return EquityTrendResult("EQUITY_TREND_REVIEW", False, 0.0, 0.0, 0.0, "FLAT", 0.0, "insufficient_equity_observations")
        values = [float(item.get("equity", 0.0) or 0.0) for item in observations]
        opening = values[0]
        closing = values[-1]
        if opening <= 0:
            return EquityTrendResult("EQUITY_TREND_REVIEW", False, opening, closing, closing - opening, "FLAT", 0.0, "opening_equity_not_positive")
        change = round(closing - opening, 6)
        strength = round(abs(change) / opening * 100.0, 4)
        if change > 0:
            direction = "UP"
        elif change < 0:
            direction = "DOWN"
        else:
            direction = "FLAT"
        return EquityTrendResult("EQUITY_TREND_READY", True, opening, closing, change, direction, strength, "equity_trend_ready")
