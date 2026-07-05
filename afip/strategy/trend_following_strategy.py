class TrendFollowingStrategy:
    name = "TrendFollowingStrategy"

    def evaluate(self, snapshot: dict) -> dict:
        closes = snapshot.get("closes", [])
        if len(closes) < 5:
            return {"strategy": self.name, "action": "WAIT", "confidence": 0, "reason": "not_enough_data"}

        rising = closes[-1] > closes[-2] > closes[-3]
        falling = closes[-1] < closes[-2] < closes[-3]

        if rising:
            return {"strategy": self.name, "action": "BUY", "confidence": 70, "reason": "recent_closes_rising"}
        if falling:
            return {"strategy": self.name, "action": "SELL", "confidence": 70, "reason": "recent_closes_falling"}
        return {"strategy": self.name, "action": "WAIT", "confidence": 35, "reason": "no_clean_trend"}
