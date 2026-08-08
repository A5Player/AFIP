"""Closed-bar market structure context for AFIP research and plan review.

The analyzer is deterministic and deliberately execution-neutral. It labels
only completed OHLC bars supplied by a caller; it neither requests MT5 data nor
authorizes an order. Short history is explicit so plan gates fail closed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class MarketStructureContext:
    timeframe: str
    regime: str
    trend_state: str
    structure_state: str
    zone_position: str
    volatility_state: str
    pattern_family: str
    pattern_name: str
    direction: str
    confidence: float
    lookback_bars: int
    latest_close: float | None
    support_price: float | None
    resistance_price: float | None
    reason: str
    research_ready: bool
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarketStructureContextAnalyzer:
    """Classify current context from the most recent closed bars only."""

    def __init__(self, minimum_bars: int = 20) -> None:
        if minimum_bars < 5:
            raise ValueError("minimum_bars_must_be_at_least_five")
        self.minimum_bars = minimum_bars

    def analyze(self, bars: Sequence[Mapping[str, Any]], *, timeframe: str) -> MarketStructureContext:
        rows: list[tuple[float, float, float, float]] = []
        for item in bars[-self.minimum_bars:]:
            values = tuple(_number(item.get(name)) for name in ("open", "high", "low", "close"))
            if any(value is None for value in values):
                continue
            open_, high, low, close = values
            if high >= low:
                rows.append((open_, high, low, close))
        key = str(timeframe or "UNKNOWN").upper()
        if len(rows) < self.minimum_bars:
            return MarketStructureContext(key, "INSUFFICIENT_DATA", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNCLASSIFIED", "INSUFFICIENT_CLOSED_BARS", "WAIT", 0.0, len(rows), None, None, None, "minimum_closed_bar_history_not_available", False)

        closes = [row[3] for row in rows]
        highs = [row[1] for row in rows]
        lows = [row[2] for row in rows]
        ranges = [max(0.0, high - low) for _, high, low, _ in rows]
        average_range = sum(ranges) / len(ranges)
        displacement = closes[-1] - closes[0]
        normalized_slope = abs(displacement) / max(average_range * len(rows), 1e-12)
        latest_range_ratio = ranges[-1] / max(average_range, 1e-12)
        support, resistance = min(lows), max(highs)
        location = (closes[-1] - support) / max(resistance - support, 1e-12)
        zone = "LOWER_ZONE" if location <= 0.30 else "UPPER_ZONE" if location >= 0.70 else "MID_ZONE"
        volatility = "HIGH" if latest_range_ratio >= 1.50 else "LOW" if latest_range_ratio <= 0.65 else "NORMAL"
        first_half, second_half = rows[: len(rows) // 2], rows[len(rows) // 2 :]
        higher_highs = max(row[1] for row in second_half) > max(row[1] for row in first_half)
        higher_lows = min(row[2] for row in second_half) >= min(row[2] for row in first_half)
        lower_lows = min(row[2] for row in second_half) < min(row[2] for row in first_half)
        lower_highs = max(row[1] for row in second_half) <= max(row[1] for row in first_half)

        if normalized_slope >= 0.35 and displacement > 0 and higher_highs and higher_lows:
            regime, trend, structure, direction = "UP_TREND", "UP", "HIGHER_HIGHS_HIGHER_LOWS", "BUY"
            family = "TREND_PULLBACK" if zone != "UPPER_ZONE" else "TREND_EXTENSION"
            name = "UPTREND_PULLBACK" if family == "TREND_PULLBACK" else "UPTREND_UPPER_ZONE_EXTENSION"
        elif normalized_slope >= 0.35 and displacement < 0 and lower_lows and lower_highs:
            regime, trend, structure, direction = "DOWN_TREND", "DOWN", "LOWER_HIGHS_LOWER_LOWS", "SELL"
            family = "TREND_PULLBACK" if zone != "LOWER_ZONE" else "TREND_EXTENSION"
            name = "DOWNTREND_PULLBACK" if family == "TREND_PULLBACK" else "DOWNTREND_LOWER_ZONE_EXTENSION"
        elif normalized_slope <= 0.18:
            regime, trend, structure, direction = "SIDEWAY", "FLAT", "RANGE_BOUND", "WAIT"
            family = "RANGE_REVERSION"
            name = "RANGE_LOWER_ZONE" if zone == "LOWER_ZONE" else "RANGE_UPPER_ZONE" if zone == "UPPER_ZONE" else "RANGE_MID_ZONE"
        else:
            regime, trend, structure, direction = "TRANSITION", "MIXED", "STRUCTURE_UNCONFIRMED", "WAIT"
            family, name = "TRANSITION", "TRANSITION_WAIT"
        confidence = round(min(100.0, 45.0 + normalized_slope * 80.0 + (10.0 if volatility != "HIGH" else 0.0)), 4)
        return MarketStructureContext(key, regime, trend, structure, zone, volatility, family, name, direction, confidence, len(rows), closes[-1], support, resistance, "closed_bar_structure_context_ready", True)
