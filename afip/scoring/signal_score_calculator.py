class SignalScoreCalculator:
    """
    Aggregates Intelligence outputs into buy/sell/wait scores.
    """

    def calculate(self, intelligence_results: list):
        buy_score = 0.0
        sell_score = 0.0
        penalties = 0.0
        reasons = []

        for result in intelligence_results:
            direction = result.get("direction")
            confidence = float(result.get("confidence", 0))

            if direction == "BUY":
                buy_score += confidence
            elif direction == "SELL":
                sell_score += confidence

            penalties += float(result.get("confidence_penalty", 0))
            if result.get("reason"):
                reasons.append(result["reason"])

        buy_score = max(0, min(100, buy_score - penalties))
        sell_score = max(0, min(100, sell_score - penalties))
        overall_confidence = max(buy_score, sell_score)

        return {
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "overall_confidence": round(overall_confidence, 2),
            "penalties": round(penalties, 2),
            "reasons": reasons,
        }
