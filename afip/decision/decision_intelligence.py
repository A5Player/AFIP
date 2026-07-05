class DecisionIntelligence:
    """
    Combines modular Intelligence outputs into a transparent final recommendation.
    """

    def decide(self, intelligence_results: list) -> dict:
        buy_score = 0.0
        sell_score = 0.0
        penalties = 0.0
        reasons = []

        for item in intelligence_results:
            direction = item.get("direction")
            confidence = float(item.get("confidence", 0))
            penalties += float(item.get("confidence_penalty", 0))
            reasons.append({
                "name": item.get("name"),
                "direction": direction,
                "confidence": confidence,
                "status": item.get("status"),
                "reason": item.get("reason"),
            })

            if direction == "BUY":
                buy_score += confidence
            elif direction == "SELL":
                sell_score += confidence

        buy_score = min(100, max(0, buy_score / max(1, len(intelligence_results) / 2)))
        sell_score = min(100, max(0, sell_score / max(1, len(intelligence_results) / 2)))
        confidence = max(buy_score, sell_score)

        if confidence < 60:
            action = "WAIT"
            decision_reason = "confidence_below_threshold"
        elif buy_score > sell_score:
            action = "BUY"
            decision_reason = "decision_intelligence_buy_edge"
        elif sell_score > buy_score:
            action = "SELL"
            decision_reason = "decision_intelligence_sell_edge"
        else:
            action = "WAIT"
            decision_reason = "no_clear_edge"

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "penalties": round(penalties, 2),
            "reason": decision_reason,
            "explain": reasons,
        }
