from __future__ import annotations


class MarketStructureIntelligence:
    """Evaluate market structure from OHLC data using financial terminology only."""

    name = "MarketStructureIntelligence"

    def analyze(self, snapshot: dict) -> dict:
        highs = [float(x) for x in snapshot.get("highs", []) if x is not None]
        lows = [float(x) for x in snapshot.get("lows", []) if x is not None]
        closes = [float(x) for x in snapshot.get("closes", []) if x is not None]

        if len(highs) < 5 or len(lows) < 5 or len(closes) < 5:
            return self._result("FLAT", 35.0, "INSUFFICIENT_DATA", "market_structure_insufficient_data")

        recent_highs = highs[-6:]
        recent_lows = lows[-6:]
        recent_closes = closes[-6:]

        higher_highs = sum(1 for previous, current in zip(recent_highs, recent_highs[1:]) if current > previous)
        higher_lows = sum(1 for previous, current in zip(recent_lows, recent_lows[1:]) if current > previous)
        lower_highs = sum(1 for previous, current in zip(recent_highs, recent_highs[1:]) if current < previous)
        lower_lows = sum(1 for previous, current in zip(recent_lows, recent_lows[1:]) if current < previous)

        latest_close = recent_closes[-1]
        previous_high = max(recent_highs[:-1])
        previous_low = min(recent_lows[:-1])

        bullish_break = latest_close > previous_high
        bearish_break = latest_close < previous_low

        if bullish_break or (higher_highs >= 3 and higher_lows >= 3 and latest_close >= recent_closes[0]):
            confidence = 65.0 + min(25.0, (higher_highs + higher_lows) * 3.0)
            return self._result("BUY", confidence, "BULLISH_STRUCTURE", "higher_highs_higher_lows")

        if bearish_break or (lower_highs >= 3 and lower_lows >= 3 and latest_close <= recent_closes[0]):
            confidence = 65.0 + min(25.0, (lower_highs + lower_lows) * 3.0)
            return self._result("SELL", confidence, "BEARISH_STRUCTURE", "lower_highs_lower_lows")

        return self._result("FLAT", 45.0, "BALANCED", "market_structure_balanced")

    def _result(self, direction: str, confidence: float, structure: str, reason: str) -> dict:
        buy_score = confidence if direction == "BUY" else 0.0
        sell_score = confidence if direction == "SELL" else 0.0
        return {
            "name": self.name,
            "status": "READY",
            "direction": direction,
            "confidence": round(float(confidence), 2),
            "structure": structure,
            "reason": reason,
            "buy_score": round(float(buy_score), 2),
            "sell_score": round(float(sell_score), 2),
        }
