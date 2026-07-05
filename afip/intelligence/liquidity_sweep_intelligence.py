"""AFIP Liquidity Sweep Intelligence.

Detects buy-side and sell-side liquidity sweeps with rejection confirmation.
"""
from __future__ import annotations


class LiquiditySweepIntelligence:
    """Evaluate equal-level sweeps and rejection quality."""

    name = "LiquiditySweepIntelligence"

    def __init__(self, lookback: int = 20, equality_tolerance_points: float = 50.0, point_size: float = 0.01):
        self.lookback = max(5, int(lookback))
        self.equality_tolerance_points = max(0.0, float(equality_tolerance_points))
        self.point_size = max(0.00001, float(point_size))

    def analyze(self, snapshot: dict) -> dict:
        highs = self._numbers(snapshot.get("highs", []))
        lows = self._numbers(snapshot.get("lows", []))
        closes = self._numbers(snapshot.get("closes", []))
        sample_count = min(len(highs), len(lows), len(closes))

        if sample_count < self.lookback:
            return self._result("FLAT", 30.0, "LEARNING", "insufficient_liquidity_sweep_samples")

        highs = highs[-self.lookback :]
        lows = lows[-self.lookback :]
        closes = closes[-self.lookback :]
        previous_high = max(highs[:-1])
        previous_low = min(lows[:-1])
        latest_high = highs[-1]
        latest_low = lows[-1]
        latest_close = closes[-1]
        tolerance = self.equality_tolerance_points * self.point_size
        equal_high_count = sum(1 for high in highs[:-1] if abs(high - previous_high) <= tolerance)
        equal_low_count = sum(1 for low in lows[:-1] if abs(low - previous_low) <= tolerance)

        buy_side_sweep = latest_high > previous_high and latest_close < previous_high
        sell_side_sweep = latest_low < previous_low and latest_close > previous_low
        if sell_side_sweep:
            sweep_depth = latest_close - latest_low
            confidence = self._confidence(equal_low_count, sweep_depth, previous_high - previous_low)
            return self._result(
                "BUY",
                confidence,
                "READY",
                "sell_side_liquidity_sweep_confirmed",
                sweep_type="SELL_SIDE_SWEEP",
                equal_level_count=equal_low_count,
                reference_level=round(previous_low, 5),
                sweep_extreme=round(latest_low, 5),
                confirmation_close=round(latest_close, 5),
            )

        if buy_side_sweep:
            sweep_depth = latest_high - latest_close
            confidence = self._confidence(equal_high_count, sweep_depth, previous_high - previous_low)
            return self._result(
                "SELL",
                confidence,
                "READY",
                "buy_side_liquidity_sweep_confirmed",
                sweep_type="BUY_SIDE_SWEEP",
                equal_level_count=equal_high_count,
                reference_level=round(previous_high, 5),
                sweep_extreme=round(latest_high, 5),
                confirmation_close=round(latest_close, 5),
            )

        return self._result(
            "FLAT",
            44.0,
            "READY",
            "no_confirmed_liquidity_sweep",
            sweep_type="NONE",
            equal_high_count=equal_high_count,
            equal_low_count=equal_low_count,
            reference_high=round(previous_high, 5),
            reference_low=round(previous_low, 5),
        )

    @staticmethod
    def _confidence(equal_level_count: int, rejection_distance: float, prior_range: float) -> float:
        pool_score = min(25.0, equal_level_count * 8.0)
        rejection_score = min(25.0, rejection_distance / prior_range * 100.0) if prior_range > 0 else 0.0
        return round(min(94.0, 55.0 + pool_score + rejection_score), 2)

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
