class CandlePatternIntelligence:
    name = "CandlePatternIntelligence"

    def analyze(self, snapshot: dict) -> dict:
        opens = snapshot.get("opens", [])
        closes = snapshot.get("closes", [])
        highs = snapshot.get("highs", [])
        lows = snapshot.get("lows", [])
        if not opens or not closes or not highs or not lows:
            return {"name": self.name, "direction": "FLAT", "confidence": 0, "reason": "not_enough_candle_data"}

        o, c, h, l = opens[-1], closes[-1], highs[-1], lows[-1]
        candle_range = max(h - l, 0.00001)
        body_ratio = abs(c - o) / candle_range
        if body_ratio < 0.25:
            return {"name": self.name, "direction": "FLAT", "confidence": 30, "reason": "weak_candle_body"}

        direction = "BUY" if c > o else "SELL" if c < o else "FLAT"
        confidence = min(80, 35 + body_ratio * 50)
        return {"name": self.name, "direction": direction, "confidence": round(confidence, 2), "body_ratio": round(body_ratio, 4), "reason": "last_candle_pressure"}
