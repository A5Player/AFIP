"""AFIP Order Block Intelligence.

Detects fresh, mitigated, and broken order block zones from OHLC data.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderBlockZone:
    """Detected order block zone."""

    direction: str
    lower_bound: float
    upper_bound: float
    state: str
    strength: float
    origin_index: int


class OrderBlockIntelligence:
    """Evaluate likely institutional order block zones."""

    name = "OrderBlockIntelligence"

    def __init__(self, lookback: int = 60):
        self.lookback = max(6, int(lookback))

    def analyze(self, snapshot: dict) -> dict:
        opens = self._numbers(snapshot.get("opens", []))
        highs = self._numbers(snapshot.get("highs", []))
        lows = self._numbers(snapshot.get("lows", []))
        closes = self._numbers(snapshot.get("closes", []))
        sample_count = min(len(opens), len(highs), len(lows), len(closes))

        if sample_count < 6:
            return self._result("FLAT", 30.0, "LEARNING", "insufficient_order_block_samples")

        opens = opens[-self.lookback :]
        highs = highs[-self.lookback :]
        lows = lows[-self.lookback :]
        closes = closes[-self.lookback :]
        zones = self._detect_zones(opens, highs, lows, closes)

        active_zones = [zone for zone in zones if zone.state != "BROKEN"]
        if not active_zones:
            return self._result("FLAT", 42.0, "READY", "no_active_order_block", active_order_block_count=0)

        latest = active_zones[-1]
        direction = "BUY" if latest.direction == "BULLISH" else "SELL"
        confidence = min(94.0, 48.0 + latest.strength * 0.42)
        if latest.state == "MITIGATED":
            confidence -= 8.0

        return self._result(
            direction,
            confidence,
            "READY",
            "active_order_block_detected",
            active_order_block_count=len(active_zones),
            latest_order_block={
                "direction": latest.direction,
                "lower_bound": round(latest.lower_bound, 5),
                "upper_bound": round(latest.upper_bound, 5),
                "state": latest.state,
                "strength": round(latest.strength, 2),
                "origin_index": latest.origin_index,
            },
        )

    def _detect_zones(self, opens: list[float], highs: list[float], lows: list[float], closes: list[float]) -> list[OrderBlockZone]:
        zones: list[OrderBlockZone] = []
        ranges = [max(0.0, high - low) for high, low in zip(highs, lows)]
        average_range = sum(ranges) / len(ranges) if ranges else 0.0
        latest_close = closes[-1]
        latest_low = lows[-1]
        latest_high = highs[-1]

        for index in range(1, len(closes) - 2):
            current_bearish = closes[index] < opens[index]
            current_bullish = closes[index] > opens[index]
            next_range = ranges[index + 1]
            displacement = next_range / average_range if average_range > 0 else 0.0
            next_bullish_break = closes[index + 1] > highs[index]
            next_bearish_break = closes[index + 1] < lows[index]

            if current_bearish and next_bullish_break and displacement >= 1.1:
                lower_bound = min(opens[index], closes[index], lows[index])
                upper_bound = max(opens[index], closes[index])
                zones.append(
                    OrderBlockZone(
                        "BULLISH",
                        lower_bound,
                        upper_bound,
                        self._bullish_state(lower_bound, upper_bound, latest_low, latest_close),
                        self._strength(displacement, ranges[index], average_range),
                        index,
                    )
                )

            if current_bullish and next_bearish_break and displacement >= 1.1:
                lower_bound = min(opens[index], closes[index])
                upper_bound = max(opens[index], closes[index], highs[index])
                zones.append(
                    OrderBlockZone(
                        "BEARISH",
                        lower_bound,
                        upper_bound,
                        self._bearish_state(lower_bound, upper_bound, latest_high, latest_close),
                        self._strength(displacement, ranges[index], average_range),
                        index,
                    )
                )
        return zones

    @staticmethod
    def _bullish_state(lower_bound: float, upper_bound: float, latest_low: float, latest_close: float) -> str:
        if latest_close < lower_bound:
            return "BROKEN"
        if latest_low <= upper_bound:
            return "MITIGATED"
        return "FRESH"

    @staticmethod
    def _bearish_state(lower_bound: float, upper_bound: float, latest_high: float, latest_close: float) -> str:
        if latest_close > upper_bound:
            return "BROKEN"
        if latest_high >= lower_bound:
            return "MITIGATED"
        return "FRESH"

    @staticmethod
    def _strength(displacement: float, origin_range: float, average_range: float) -> float:
        compact_origin_bonus = 20.0 if average_range > 0 and origin_range <= average_range else 0.0
        return min(100.0, displacement * 38.0 + compact_origin_bonus)

    @staticmethod
    def _numbers(values: object) -> list[float]:
        return [float(value) for value in values or [] if value is not None]

    def _result(self, direction: str, confidence: float, status: str, reason: str, **extra: object) -> dict:
        buy_score = confidence if direction == "BUY" else 0.0
        sell_score = confidence if direction == "SELL" else 0.0
        result = {
            "name": self.name,
            "status": status,
            "direction": direction,
            "confidence": round(float(confidence), 2),
            "reason": reason,
            "buy_score": round(float(buy_score), 2),
            "sell_score": round(float(sell_score), 2),
        }
        result.update(extra)
        return result
