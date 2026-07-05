"""Signal quality engine for AFIP decision readiness."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp, numbers


class SignalQualityEngine:
    """Score trend stability, candle quality, and signal consistency."""

    name = "SignalQualityEngine"

    def evaluate(self, snapshot: dict) -> dict:
        closes = numbers(snapshot.get("closes"))
        highs = numbers(snapshot.get("highs"))
        lows = numbers(snapshot.get("lows"))
        if len(closes) < 5 or len(highs) < 5 or len(lows) < 5:
            return EngineResult(self.name, "LEARNING", "WAIT", 32.0, "insufficient_signal_samples", {}).as_dict()
        direction = "BUY" if closes[-1] > closes[0] else "SELL" if closes[-1] < closes[0] else "WAIT"
        consistency = self._consistency(closes)
        candle_quality = self._candle_quality(highs, lows, closes)
        confidence = clamp(35.0 + consistency * 0.35 + candle_quality * 0.35)
        if confidence < 55:
            direction = "WAIT"
        return EngineResult(
            self.name,
            "READY",
            direction,
            confidence,
            "signal_quality_ready" if direction != "WAIT" else "signal_quality_wait",
            {"consistency_score": consistency, "candle_quality_score": candle_quality},
        ).as_dict()

    @staticmethod
    def _consistency(closes: list[float]) -> float:
        moves = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
        positive = sum(1 for move in moves if move > 0)
        negative = sum(1 for move in moves if move < 0)
        return clamp(max(positive, negative) / max(1, len(moves)) * 100.0)

    @staticmethod
    def _candle_quality(highs: list[float], lows: list[float], closes: list[float]) -> float:
        ranges = [max(0.0, high - low) for high, low in zip(highs, lows)]
        average_range = sum(ranges) / max(1, len(ranges))
        latest_range = ranges[-1]
        if average_range <= 0:
            return 0.0
        range_score = min(100.0, latest_range / average_range * 60.0)
        close_position = (closes[-1] - lows[-1]) / latest_range * 100.0 if latest_range > 0 else 50.0
        close_quality = abs(close_position - 50.0) * 2.0
        return clamp((range_score + close_quality) / 2.0)
