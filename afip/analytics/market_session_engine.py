"""Market session classification for reporting and analytics."""
from __future__ import annotations


class MarketSessionEngine:
    """Classify UTC hour into broad global market sessions."""

    name = "MarketSessionEngine"

    def evaluate(self, hour_utc: int) -> dict:
        hour = int(hour_utc) % 24
        if 0 <= hour < 7:
            session = "ASIA"
        elif 7 <= hour < 12:
            session = "EUROPE_OPEN"
        elif 12 <= hour < 17:
            session = "US_EUROPE_OVERLAP"
        elif 17 <= hour < 21:
            session = "US_SESSION"
        else:
            session = "LATE_US_ASIA_TRANSITION"
        return {"name": self.name, "status": "READY", "hour_utc": hour, "session": session}
