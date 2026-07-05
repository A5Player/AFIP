class StrategyAggregator:
    def aggregate(self, strategy_results: list) -> dict:
        buy = 0.0
        sell = 0.0
        reasons = []

        for item in strategy_results:
            action = item.get("action")
            confidence = float(item.get("confidence", 0))
            if action == "BUY":
                buy += confidence
            elif action == "SELL":
                sell += confidence
            reasons.append(item.get("reason", "unknown"))

        if buy > sell and buy >= 60:
            action = "BUY"
            confidence = min(100, buy)
        elif sell > buy and sell >= 60:
            action = "SELL"
            confidence = min(100, sell)
        else:
            action = "WAIT"
            confidence = max(buy, sell)

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "buy_score": round(min(100, buy), 2),
            "sell_score": round(min(100, sell), 2),
            "reasons": reasons,
        }
