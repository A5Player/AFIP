"""AFIP Imbalance Intelligence.

Measures directional candle imbalance and market efficiency from OHLC data.
"""
from __future__ import annotations


class ImbalanceIntelligence:
    """Evaluate expansion strength, directional imbalance, and efficiency."""

    name = "ImbalanceIntelligence"

    def __init__(self, lookback: int = 20):
        self.lookback = max(5, int(lookback))

    def analyze(self, snapshot: dict) -> dict:
        opens = self._numbers(snapshot.get("opens", []))
        highs = self._numbers(snapshot.get("highs", []))
        lows = self._numbers(snapshot.get("lows", []))
        closes = self._numbers(snapshot.get("closes", []))
        sample_count = min(len(opens), len(highs), len(lows), len(closes))

        if sample_count < 5:
            return self._result("FLAT", 30.0, "LEARNING", "insufficient_imbalance_samples")

        opens = opens[-self.lookback :]
        highs = highs[-self.lookback :]
        lows = lows[-self.lookback :]
        closes = closes[-self.lookback :]
        bodies = [abs(close - open_) for open_, close in zip(opens, closes)]
        ranges = [max(0.0, high - low) for high, low in zip(highs, lows)]
        average_range = sum(ranges) / len(ranges) if ranges else 0.0
        average_body = sum(bodies) / len(bodies) if bodies else 0.0
        latest_body = bodies[-1]
        latest_range = ranges[-1]
        body_ratio = latest_body / latest_range if latest_range > 0 else 0.0
        expansion_strength = min(100.0, latest_range / average_range * 50.0) if average_range > 0 else 0.0
        directional_move = closes[-1] - closes[0]
        total_path = sum(abs(current - previous) for previous, current in zip(closes, closes[1:]))
        efficiency_score = abs(directional_move) / total_path * 100.0 if total_path > 0 else 0.0
        bullish_pressure = sum(max(0.0, close - open_) for open_, close in zip(opens, closes))
        bearish_pressure = sum(max(0.0, open_ - close) for open_, close in zip(opens, closes))
        pressure_total = bullish_pressure + bearish_pressure
        imbalance_score = abs(bullish_pressure - bearish_pressure) / pressure_total * 100.0 if pressure_total > 0 else 0.0

        direction = "FLAT"
        if bullish_pressure > bearish_pressure and closes[-1] > closes[0]:
            direction = "BUY"
        elif bearish_pressure > bullish_pressure and closes[-1] < closes[0]:
            direction = "SELL"

        confidence = 40.0 + imbalance_score * 0.25 + efficiency_score * 0.2 + expansion_strength * 0.15
        if body_ratio < 0.35:
            confidence -= 10.0
        confidence = max(0.0, min(92.0, confidence))

        state = "STRONG_EXPANSION" if expansion_strength >= 70.0 and body_ratio >= 0.55 else "NORMAL_IMBALANCE"
        if imbalance_score < 18.0 or efficiency_score < 20.0:
            direction = "FLAT"
            state = "BALANCED_FLOW"
            confidence = min(confidence, 48.0)

        return self._result(
            direction,
            confidence,
            "READY",
            "imbalance_evaluated",
            imbalance_state=state,
            imbalance_score=round(imbalance_score, 2),
            efficiency_score=round(efficiency_score, 2),
            expansion_strength=round(expansion_strength, 2),
            body_ratio=round(body_ratio, 4),
            average_body=round(average_body, 5),
        )

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
