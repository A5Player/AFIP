class RiskAwareDecisionService:
    def decide(self, base_decision: dict, risk_assessment: dict) -> dict:
        if not risk_assessment.get("allowed", False):
            return {
                "action": "WAIT",
                "confidence": base_decision.get("confidence", 0),
                "reason": "risk_block",
                "risk": risk_assessment,
                "base_decision": base_decision,
            }

        return {
            "action": base_decision.get("action", "WAIT"),
            "confidence": base_decision.get("confidence", 0),
            "reason": base_decision.get("reason", "risk_pass"),
            "risk": risk_assessment,
            "base_decision": base_decision,
        }
