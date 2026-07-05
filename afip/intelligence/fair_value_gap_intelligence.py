"""AFIP Fair Value Gap Intelligence.

Detects three-candle fair value gaps from OHLC data using financial market
terminology only. This component is read-only and does not execute orders.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FairValueGapZone:
    """Detected fair value gap zone."""

    direction: str
    lower_bound: float
    upper_bound: float
    gap_size: float
    fill_percent: float
    state: str
    origin_index: int


class FairValueGapIntelligence:
    """Evaluate bullish and bearish fair value gaps from OHLC samples."""

    name = "FairValueGapIntelligence"

    def __init__(self, minimum_gap_points: float = 10.0, point_size: float = 0.01, lookback: int = 80):
        self.minimum_gap_points = max(0.0, float(minimum_gap_points))
        self.point_size = max(0.00001, float(point_size))
        self.lookback = max(3, int(lookback))

    def analyze(self, snapshot: dict) -> dict:
        highs = self._numbers(snapshot.get("highs", []))
        lows = self._numbers(snapshot.get("lows", []))
        closes = self._numbers(snapshot.get("closes", []))

        sample_count = min(len(highs), len(lows), len(closes))
        if sample_count < 3:
            return self._result("FLAT", 25.0, "LEARNING", "insufficient_fvg_samples")

        highs = highs[-self.lookback :]
        lows = lows[-self.lookback :]
        closes = closes[-self.lookback :]
        zones = self._detect_zones(highs, lows)

        if not zones:
            return self._result(
                "FLAT",
                42.0,
                "READY",
                "no_active_fair_value_gap",
                active_gap_count=0,
                latest_gap=None,
            )

        latest = zones[-1]
        displacement = self._displacement_score(highs, lows, closes, latest.origin_index)
        fill_quality = max(0.0, 100.0 - latest.fill_percent)
        gap_points = latest.gap_size / self.point_size
        gap_quality = min(100.0, gap_points * 2.5)
        confidence = min(94.0, 45.0 + gap_quality * 0.25 + fill_quality * 0.2 + displacement * 0.25)

        direction = "BUY" if latest.direction == "BULLISH" else "SELL"
        if latest.state == "FILLED":
            direction = "FLAT"
            confidence = min(confidence, 45.0)

        return self._result(
            direction,
            confidence,
            "READY",
            "active_fair_value_gap_detected",
            active_gap_count=len([zone for zone in zones if zone.state != "FILLED"]),
            latest_gap=self._zone_dict(latest),
            gap_quality=round(gap_quality, 2),
            displacement_score=round(displacement, 2),
        )

    def _detect_zones(self, highs: list[float], lows: list[float]) -> list[FairValueGapZone]:
        zones: list[FairValueGapZone] = []
        minimum_gap = self.minimum_gap_points * self.point_size
        last_low = lows[-1]
        last_high = highs[-1]

        for index in range(2, min(len(highs), len(lows))):
            first_high = highs[index - 2]
            first_low = lows[index - 2]
            third_high = highs[index]
            third_low = lows[index]

            if third_low > first_high and third_low - first_high >= minimum_gap:
                lower_bound = first_high
                upper_bound = third_low
                zones.append(
                    FairValueGapZone(
                        direction="BULLISH",
                        lower_bound=lower_bound,
                        upper_bound=upper_bound,
                        gap_size=upper_bound - lower_bound,
                        fill_percent=self._bullish_fill_percent(lower_bound, upper_bound, last_low),
                        state=self._bullish_state(lower_bound, upper_bound, last_low),
                        origin_index=index,
                    )
                )

            if third_high < first_low and first_low - third_high >= minimum_gap:
                lower_bound = third_high
                upper_bound = first_low
                zones.append(
                    FairValueGapZone(
                        direction="BEARISH",
                        lower_bound=lower_bound,
                        upper_bound=upper_bound,
                        gap_size=upper_bound - lower_bound,
                        fill_percent=self._bearish_fill_percent(lower_bound, upper_bound, last_high),
                        state=self._bearish_state(lower_bound, upper_bound, last_high),
                        origin_index=index,
                    )
                )
        return zones

    @staticmethod
    def _bullish_state(lower_bound: float, upper_bound: float, last_low: float) -> str:
        if last_low <= lower_bound:
            return "FILLED"
        if last_low < upper_bound:
            return "PARTIALLY_FILLED"
        return "UNTOUCHED"

    @staticmethod
    def _bearish_state(lower_bound: float, upper_bound: float, last_high: float) -> str:
        if last_high >= upper_bound:
            return "FILLED"
        if last_high > lower_bound:
            return "PARTIALLY_FILLED"
        return "UNTOUCHED"

    @staticmethod
    def _bullish_fill_percent(lower_bound: float, upper_bound: float, last_low: float) -> float:
        if upper_bound <= lower_bound:
            return 100.0
        if last_low >= upper_bound:
            return 0.0
        return round(min(100.0, max(0.0, (upper_bound - last_low) / (upper_bound - lower_bound) * 100.0)), 2)

    @staticmethod
    def _bearish_fill_percent(lower_bound: float, upper_bound: float, last_high: float) -> float:
        if upper_bound <= lower_bound:
            return 100.0
        if last_high <= lower_bound:
            return 0.0
        return round(min(100.0, max(0.0, (last_high - lower_bound) / (upper_bound - lower_bound) * 100.0)), 2)

    @staticmethod
    def _displacement_score(highs: list[float], lows: list[float], closes: list[float], index: int) -> float:
        ranges = [max(0.0, high - low) for high, low in zip(highs, lows)]
        if not ranges or index >= len(ranges):
            return 0.0
        average_range = sum(ranges) / len(ranges)
        if average_range <= 0:
            return 0.0
        candle_range = ranges[index]
        body = abs(closes[index] - closes[index - 1]) if index > 0 and index < len(closes) else candle_range
        return round(min(100.0, ((candle_range + body) / (2.0 * average_range)) * 55.0), 2)

    @staticmethod
    def _numbers(values: object) -> list[float]:
        return [float(value) for value in values or [] if value is not None]

    @staticmethod
    def _zone_dict(zone: FairValueGapZone) -> dict:
        return {
            "direction": zone.direction,
            "lower_bound": round(zone.lower_bound, 5),
            "upper_bound": round(zone.upper_bound, 5),
            "gap_size": round(zone.gap_size, 5),
            "fill_percent": round(zone.fill_percent, 2),
            "state": zone.state,
            "origin_index": zone.origin_index,
        }

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
