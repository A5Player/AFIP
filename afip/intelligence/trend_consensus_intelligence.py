from afip.intelligence.trend_intelligence import TrendIntelligence

class TrendConsensusIntelligence:
    name = "TrendConsensusIntelligence"

    def __init__(self, trend_intelligence=None):
        self.trend_intelligence = trend_intelligence or TrendIntelligence()

    def analyze(self, timeframe_snapshots: dict) -> dict:
        results = {}
        buy_votes = 0
        sell_votes = 0
        confidence_total = 0.0

        for timeframe, snapshot in timeframe_snapshots.items():
            result = self.trend_intelligence.analyze(snapshot)
            results[timeframe] = result
            direction = result.get("direction")
            confidence = float(result.get("confidence", 0))
            confidence_total += confidence

            if direction == "BUY":
                buy_votes += 1
            elif direction == "SELL":
                sell_votes += 1

        if buy_votes > sell_votes:
            direction = "BUY"
        elif sell_votes > buy_votes:
            direction = "SELL"
        else:
            direction = "FLAT"

        count = max(len(timeframe_snapshots), 1)
        return {
            "name": self.name,
            "direction": direction,
            "confidence": round(confidence_total / count, 2),
            "buy_votes": buy_votes,
            "sell_votes": sell_votes,
            "timeframes": results,
            "reason": "multi_timeframe_trend_consensus",
        }
