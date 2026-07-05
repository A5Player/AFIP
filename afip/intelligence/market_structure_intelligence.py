"""
AFIP Market Structure Intelligence.

Evaluates price structure from OHLC data using financial market terminology.
This component is read-only and does not execute orders.
"""

from __future__ import annotations


class MarketStructureIntelligence:
    """
    Detects directional market structure using swing points and structure breaks.

    Output is designed for the AFIP Modular Intelligence pipeline:
    - direction: BUY, SELL, or FLAT
    - confidence: 0.0 to 100.0
    - status: READY, LEARNING, or CAUTION
    """

    name = "MarketStructureIntelligence"

    def __init__(self, lookback: int = 3):
        self.lookback = max(1, int(lookback))

    def analyze(self, snapshot: dict) -> dict:
        highs = [float(value) for value in snapshot.get("highs", []) if value is not None]
        lows = [float(value) for value in snapshot.get("lows", []) if value is not None]
        closes = [float(value) for value in snapshot.get("closes", []) if value is not None]

        if len(highs) < 7 or len(lows) < 7 or len(closes) < 7:
            return self._result(
                direction="FLAT",
                confidence=30.0,
                status="LEARNING",
                reason="insufficient_market_structure_samples",
                structure_state="UNCONFIRMED",
                swing_highs=[],
                swing_lows=[],
            )

        swing_highs = self._swing_highs(highs)
        swing_lows = self._swing_lows(lows)
        last_close = closes[-1]

        direction = "FLAT"
        structure_state = "BALANCED"
        confidence = 45.0
        reason = "market_structure_balanced"

        last_swing_high = swing_highs[-1]["price"] if swing_highs else None
        previous_swing_high = swing_highs[-2]["price"] if len(swing_highs) >= 2 else None
        last_swing_low = swing_lows[-1]["price"] if swing_lows else None
        previous_swing_low = swing_lows[-2]["price"] if len(swing_lows) >= 2 else None

        higher_high = self._greater(last_swing_high, previous_swing_high)
        higher_low = self._greater(last_swing_low, previous_swing_low)
        lower_high = self._less(last_swing_high, previous_swing_high)
        lower_low = self._less(last_swing_low, previous_swing_low)

        if higher_high and higher_low:
            direction = "BUY"
            structure_state = "BULLISH_STRUCTURE"
            confidence = 70.0
            reason = "higher_high_and_higher_low"
        elif lower_high and lower_low:
            direction = "SELL"
            structure_state = "BEARISH_STRUCTURE"
            confidence = 70.0
            reason = "lower_high_and_lower_low"

        if last_swing_high is not None and last_close > last_swing_high:
            direction = "BUY"
            structure_state = "BULLISH_STRUCTURE_BREAK"
            confidence = max(confidence, 82.0)
            reason = "close_above_recent_swing_high"
        elif last_swing_low is not None and last_close < last_swing_low:
            direction = "SELL"
            structure_state = "BEARISH_STRUCTURE_BREAK"
            confidence = max(confidence, 82.0)
            reason = "close_below_recent_swing_low"

        compression_penalty = self._compression_penalty(highs, lows, closes)
        confidence = max(0.0, confidence - compression_penalty)
        status = "READY" if compression_penalty < 20.0 else "CAUTION"

        return self._result(
            direction=direction,
            confidence=round(confidence, 2),
            status=status,
            reason=reason,
            structure_state=structure_state,
            swing_highs=swing_highs[-3:],
            swing_lows=swing_lows[-3:],
            compression_penalty=round(compression_penalty, 2),
        )

    def _swing_highs(self, highs: list[float]) -> list[dict]:
        points = []
        for index in range(self.lookback, len(highs) - self.lookback):
            window = highs[index - self.lookback : index + self.lookback + 1]
            if highs[index] == max(window) and window.count(highs[index]) == 1:
                points.append({"index": index, "price": highs[index]})
        return points

    def _swing_lows(self, lows: list[float]) -> list[dict]:
        points = []
        for index in range(self.lookback, len(lows) - self.lookback):
            window = lows[index - self.lookback : index + self.lookback + 1]
            if lows[index] == min(window) and window.count(lows[index]) == 1:
                points.append({"index": index, "price": lows[index]})
        return points

    @staticmethod
    def _greater(current, previous) -> bool:
        return current is not None and previous is not None and current > previous

    @staticmethod
    def _less(current, previous) -> bool:
        return current is not None and previous is not None and current < previous

    @staticmethod
    def _compression_penalty(highs: list[float], lows: list[float], closes: list[float]) -> float:
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        last_close = closes[-1]
        if last_close <= 0:
            return 15.0
        range_pct = (recent_high - recent_low) / last_close * 100.0
        if range_pct < 0.08:
            return 20.0
        if range_pct < 0.15:
            return 10.0
        return 0.0

    @staticmethod
    def _result(**kwargs) -> dict:
        return {
            "name": MarketStructureIntelligence.name,
            "direction": kwargs.get("direction", "FLAT"),
            "confidence": kwargs.get("confidence", 0.0),
            "status": kwargs.get("status", "READY"),
            "reason": kwargs.get("reason", "market_structure_evaluated"),
            "structure_state": kwargs.get("structure_state", "UNCONFIRMED"),
            "swing_highs": kwargs.get("swing_highs", []),
            "swing_lows": kwargs.get("swing_lows", []),
            "compression_penalty": kwargs.get("compression_penalty", 0.0),
        }
