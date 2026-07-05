class MeanReversionStrategy:
    name = "MeanReversionStrategy"

    def evaluate(self, snapshot: dict) -> dict:
        closes = snapshot.get("closes", [])
        if len(closes) < 5:
            return {"strategy": self.name, "action": "WAIT", "confidence": 0, "reason": "not_enough_data"}

        avg = sum(closes[-5:]) / 5
        last = closes[-1]
        distance = last - avg

        if distance > 1.5:
            return {"strategy": self.name, "action": "SELL", "confidence": 55, "reason": "price_above_short_average"}
        if distance < -1.5:
            return {"strategy": self.name, "action": "BUY", "confidence": 55, "reason": "price_below_short_average"}
        return {"strategy": self.name, "action": "WAIT", "confidence": 30, "reason": "near_average"}
