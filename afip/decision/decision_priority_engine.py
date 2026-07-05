"""Decision priority ranking for financial execution readiness."""

from dataclasses import dataclass
from typing import Mapping, Any

@dataclass(frozen=True)
class DecisionPriorityResult:
    status: str
    priority: str
    priority_score: float
    reason: str

class DecisionPriorityEngine:
    """Ranks decision priority using confidence, liquidity, volatility, and risk state."""

    def rank(self, decision: Mapping[str, Any]) -> DecisionPriorityResult:
        confidence = max(0.0, min(100.0, float(decision.get("confidence", 0.0))))
        liquidity = max(0.0, min(100.0, float(decision.get("liquidity_score", 50.0))))
        volatility = max(0.0, min(100.0, float(decision.get("volatility_score", 50.0))))
        risk = str(decision.get("risk_status", "ACCEPTABLE")).upper()
        risk_modifier = 1.0 if risk == "ACCEPTABLE" else 0.65 if risk == "CAUTION" else 0.25
        score = round((confidence * 0.50 + liquidity * 0.25 + (100.0 - abs(volatility - 50.0)) * 0.25) * risk_modifier, 2)
        if score >= 75:
            priority = "HIGH"
        elif score >= 50:
            priority = "MODERATE"
        else:
            priority = "LOW"
        status = "DECISION_PRIORITY_READY" if priority != "LOW" else "DECISION_PRIORITY_REVIEW"
        return DecisionPriorityResult(status, priority, score, f"decision_priority_{priority.lower()}")
