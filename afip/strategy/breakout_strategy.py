class BreakoutStrategy:
    name = "BreakoutStrategy"

    def evaluate(self, snapshot: dict) -> dict:
        closes = snapshot.get("closes", [])
        highs = snapshot.get("highs", [])
        lows = snapshot.get("lows", [])
        if len(closes) < 5 or len(highs) < 5 or len(lows) < 5:
            return {"strategy": self.name, "action": "WAIT", "confidence": 0, "reason": "not_enough_data"}

        last_close = closes[-1]
        prior_high = max(highs[:-1])
        prior_low = min(lows[:-1])

        if last_close > prior_high:
            return {"strategy": self.name, "action": "BUY", "confidence": 75, "reason": "close_breaks_prior_high"}
        if last_close < prior_low:
            return {"strategy": self.name, "action": "SELL", "confidence": 75, "reason": "close_breaks_prior_low"}
        return {"strategy": self.name, "action": "WAIT", "confidence": 40, "reason": "no_breakout"}
