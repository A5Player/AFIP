from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionReadinessResult:
    status: str
    readiness: str
    readiness_score: float
    reason: str


class ExecutionReadinessAssessment:
    """Assess whether a unified decision is ready for execution allocation."""

    def assess(
        self,
        action: str = "WAIT",
        confidence: float = 0.0,
        risk_status: str = "ACCEPTED",
        timing: str = "IMMEDIATE",
        strategy: str = "BREAKOUT_CONTINUATION",
    ) -> ExecutionReadinessResult:
        normalized_action = str(action or "WAIT").upper()
        risk = str(risk_status or "ACCEPTED").upper()
        execution_timing = str(timing or "DELAY").upper()
        strategy_value = str(strategy or "NO_EXECUTION").upper()
        confidence_ratio = self._ratio(confidence)

        if normalized_action in {"WAIT", "NO_ACTION", "FLAT"} or risk != "ACCEPTED" or strategy_value == "NO_EXECUTION":
            return ExecutionReadinessResult(
                status="EXECUTION_READINESS_REVIEW",
                readiness="NOT_READY",
                readiness_score=0.0,
                reason="execution_requirements_not_met",
            )

        timing_score = 1.0 if execution_timing == "IMMEDIATE" else 0.72 if execution_timing == "SELECTIVE" else 0.38
        risk_score = 1.0 if risk == "ACCEPTED" else 0.0
        readiness_score = round((confidence_ratio * 0.50) + (timing_score * 0.30) + (risk_score * 0.20), 4)
        if readiness_score >= 0.78:
            readiness = "READY"
            status = "EXECUTION_READINESS_READY"
            reason = "decision_execution_aligned"
        elif readiness_score >= 0.55:
            readiness = "SELECTIVE"
            status = "EXECUTION_READINESS_SELECTIVE"
            reason = "selective_execution_allocation"
        else:
            readiness = "NOT_READY"
            status = "EXECUTION_READINESS_REVIEW"
            reason = "readiness_score_below_threshold"
        return ExecutionReadinessResult(status=status, readiness=readiness, readiness_score=readiness_score, reason=reason)

    @staticmethod
    def _ratio(value: float) -> float:
        number = float(value or 0.0)
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))
