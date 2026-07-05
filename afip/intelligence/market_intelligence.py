class MarketIntelligence:
    """
    Foundation implementation.
    Converts raw market snapshot into normalized signals.
    """

    def analyze(self, snapshot: dict):
        trend = snapshot.get("trend", "UNKNOWN")
        spread = snapshot.get("spread", 0)

        confidence = 60.0
        if spread > 30:
            confidence -= 20

        return {
            "trend": trend,
            "spread": spread,
            "confidence": max(confidence, 0),
        }
