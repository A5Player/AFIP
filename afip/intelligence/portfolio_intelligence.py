class PortfolioIntelligence:
    """
    AFIP modular Intelligence component.

    Role:
    - Produces transparent directional or risk information.
    - SIMULATION-safe by default.
    - No order execution.
    """

    name = "PortfolioIntelligence"

    def analyze(self, snapshot: dict) -> dict:
        closes = snapshot.get("closes", [])
        highs = snapshot.get("highs", [])
        lows = snapshot.get("lows", [])
        volumes = snapshot.get("volumes", [])
        spread = float(snapshot.get("spread", 999))

        direction = "FLAT"
        confidence = 35.0
        penalty = 0.0
        status = "READY"

        if len(closes) >= 3:
            recent_move = closes[-1] - closes[-3]
            if recent_move > 0:
                direction = "BUY"
            elif recent_move < 0:
                direction = "SELL"
            confidence = min(85.0, 45.0 + abs(recent_move) * 15.0)

        if highs and lows and closes and closes[-1]:
            range_pct = (max(highs[-5:]) - min(lows[-5:])) / closes[-1] * 100
            if range_pct > 1.2:
                penalty += 8.0

        if volumes:
            recent_volume = volumes[-1]
            avg_volume = sum(volumes) / len(volumes)
            if avg_volume and recent_volume > avg_volume:
                confidence = min(90.0, confidence + 5.0)

        if spread > 35:
            penalty += 25.0
            status = "CAUTION"

        return {
            "name": self.name,
            "direction": direction,
            "confidence": round(max(0.0, confidence - penalty), 2),
            "confidence_penalty": round(penalty, 2),
            "status": status,
            "reason": "portfolio_capacity_simulation",
        }
