class VolatilityIntelligence:
    """
    Estimates volatility risk from recent high-low range.
    High volatility reduces trade confidence.
    """
    name = "VolatilityIntelligence"

    def analyze(self, snapshot: dict):
        highs = snapshot.get("highs", [])
        lows = snapshot.get("lows", [])
        closes = snapshot.get("closes", [])

        if not highs or not lows or not closes:
            return {"name": self.name, "risk": "UNKNOWN", "confidence": 0, "reason": "not_enough_data"}

        recent_range = max(highs[-5:]) - min(lows[-5:])
        price = closes[-1]
        range_pct = (recent_range / price) * 100 if price else 0

        if range_pct >= 1.2:
            risk = "HIGH"
            confidence_penalty = 30
        elif range_pct >= 0.6:
            risk = "NORMAL"
            confidence_penalty = 10
        else:
            risk = "LOW"
            confidence_penalty = 0

        return {
            "name": self.name,
            "risk": risk,
            "range_pct": round(range_pct, 4),
            "confidence_penalty": confidence_penalty,
            "reason": "recent_range_volatility",
        }
