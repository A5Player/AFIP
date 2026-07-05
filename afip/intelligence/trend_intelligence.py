class TrendIntelligence:
    """
    Calculates simple trend direction from closing prices.
    Input:
        snapshot = {"closes": [float, ...]}
    Output:
        direction: BUY / SELL / FLAT
        confidence: 0-100
    """
    name = "TrendIntelligence"

    def analyze(self, snapshot: dict):
        closes = snapshot.get("closes", [])
        if len(closes) < 3:
            return {"name": self.name, "direction": "FLAT", "confidence": 0, "reason": "not_enough_data"}

        short_move = closes[-1] - closes[-3]
        long_move = closes[-1] - closes[0]

        if short_move > 0 and long_move > 0:
            direction = "BUY"
            confidence = min(90, 50 + abs(long_move) * 10)
        elif short_move < 0 and long_move < 0:
            direction = "SELL"
            confidence = min(90, 50 + abs(long_move) * 10)
        else:
            direction = "FLAT"
            confidence = 35

        return {
            "name": self.name,
            "direction": direction,
            "confidence": round(confidence, 2),
            "reason": "trend_from_recent_closes",
        }
