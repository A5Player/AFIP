class MarketRegimeIntelligence:
    name = "MarketRegimeIntelligence"

    def analyze(self, timeframe_snapshots: dict) -> dict:
        ranges = []
        for snapshot in timeframe_snapshots.values():
            highs = snapshot.get("highs", [])
            lows = snapshot.get("lows", [])
            closes = snapshot.get("closes", [])
            if highs and lows and closes and closes[-1] != 0:
                ranges.append((max(highs) - min(lows)) / closes[-1] * 100)

        if not ranges:
            return {"name": self.name, "regime": "UNKNOWN", "confidence": 0, "reason": "not_enough_data"}

        avg_range = sum(ranges) / len(ranges)
        if avg_range >= 1.2:
            regime = "EXPANSION"
            confidence = 75
        elif avg_range >= 0.45:
            regime = "NORMAL"
            confidence = 60
        else:
            regime = "QUIET"
            confidence = 45

        return {
            "name": self.name,
            "regime": regime,
            "avg_range_pct": round(avg_range, 4),
            "confidence": confidence,
            "reason": "multi_timeframe_range_regime",
        }
