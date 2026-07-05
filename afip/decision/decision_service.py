class DecisionService:
    """
    Converts scores into an actionable simulation decision.
    Live execution remains disabled outside the execution layer.
    """

    def decide(self, score: dict):
        buy = score.get("buy_score", 0)
        sell = score.get("sell_score", 0)
        confidence = score.get("overall_confidence", 0)

        if confidence < 60:
            action = "WAIT"
            reason = "confidence_below_threshold"
        elif buy > sell:
            action = "BUY"
            reason = "buy_score_dominates"
        elif sell > buy:
            action = "SELL"
            reason = "sell_score_dominates"
        else:
            action = "WAIT"
            reason = "no_direction_edge"

        return {
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "score": score,
        }
