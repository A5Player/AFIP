class MomentumIntelligence:
    """
    Measures recent price acceleration from closes.
    """
    name = "MomentumIntelligence"

    def analyze(self, snapshot: dict):
        closes = snapshot.get("closes", [])
        if len(closes) < 4:
            return {"name": self.name, "direction": "FLAT", "confidence": 0, "reason": "not_enough_data"}

        prev_move = closes[-2] - closes[-4]
        current_move = closes[-1] - closes[-3]
        acceleration = current_move - prev_move

        if acceleration > 0:
            direction = "BUY"
        elif acceleration < 0:
            direction = "SELL"
        else:
            direction = "FLAT"

        confidence = min(85, 40 + abs(acceleration) * 20)

        return {
            "name": self.name,
            "direction": direction,
            "confidence": round(confidence, 2),
            "acceleration": round(acceleration, 5),
            "reason": "recent_momentum_acceleration",
        }
