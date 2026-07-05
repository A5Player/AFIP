"""Executive decision reporting for AFIP production workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutiveDecisionReportResult:
    status: str
    action: str
    confidence: float
    readiness_score: float
    risk_status: str
    position_size: float
    reason: str
    lines: tuple[str, ...]


class ExecutiveDecisionReport:
    """Build compact report lines for production decision review."""

    def build(self, decision: dict[str, Any], readiness: dict[str, Any], risk: dict[str, Any]) -> ExecutiveDecisionReportResult:
        action = str(decision.get("action", "WAIT"))
        confidence = round(float(decision.get("confidence", 0.0)), 2)
        readiness_score = round(float(readiness.get("score", readiness.get("readiness_score", 0.0))), 2)
        risk_status = str(risk.get("status", "UNKNOWN"))
        position_size = round(float(risk.get("position_size", risk.get("lot", 0.0))), 4)

        status = "READY" if action in {"BUY", "SELL"} and readiness_score >= 70 and risk_status == "PASS" else "WAIT"
        reason = "production_decision_ready" if status == "READY" else "production_decision_not_ready"

        lines = (
            f"Decision Action: {action}",
            f"Decision Confidence: {confidence}",
            f"Readiness Score: {readiness_score}",
            f"Risk Status: {risk_status}",
            f"Position Size: {position_size}",
            f"Status: {status}",
        )

        return ExecutiveDecisionReportResult(
            status=status,
            action=action,
            confidence=confidence,
            readiness_score=readiness_score,
            risk_status=risk_status,
            position_size=position_size,
            reason=reason,
            lines=lines,
        )
