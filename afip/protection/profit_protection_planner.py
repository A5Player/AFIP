class ProfitProtectionPlanner:
    def plan(self, floating_points: float, confidence: float) -> dict:
        if floating_points <= 0:
            return {"action": "WAIT", "lock_points": 0, "reason": "no_profit"}

        if confidence < 50:
            lock_ratio = 0.75
            action = "PROTECT_AGGRESSIVE"
        elif confidence < 70:
            lock_ratio = 0.50
            action = "PROTECT_NORMAL"
        else:
            lock_ratio = 0.30
            action = "LET_PROFIT_RUN"

        return {
            "action": action,
            "lock_points": round(floating_points * lock_ratio, 2),
            "floating_points": floating_points,
            "confidence": confidence,
            "reason": "confidence_based_profit_protection",
        }
