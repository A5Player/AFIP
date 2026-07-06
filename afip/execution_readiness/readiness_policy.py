"""Deterministic policy for decision-to-execution readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .readiness_checks import ReadinessCheckResult
from .readiness_input import ExecutionReadinessInput


@dataclass(frozen=True)
class ExecutionReadinessDecision:
    status: str
    action: str
    readiness_score: float
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "readiness_score": self.readiness_score,
            "reasons": list(self.reasons),
        }


class ExecutionReadinessPolicy:
    minimum_decision_confidence = 60.0
    minimum_decision_score = 55.0
    minimum_readiness_score = 50.0

    def decide(self, value: ExecutionReadinessInput, checks: list[ReadinessCheckResult]) -> ExecutionReadinessDecision:
        if not value.has_action:
            return ExecutionReadinessDecision("EXECUTION_WAIT", "WAIT", 0.0, ("decision_action_required_before_execution",))
        if value.decision_confidence < self.minimum_decision_confidence:
            return ExecutionReadinessDecision("EXECUTION_WAIT", "WAIT", value.decision_confidence, ("decision_confidence_below_execution_floor",))
        if value.decision_score < self.minimum_decision_score:
            return ExecutionReadinessDecision("EXECUTION_WAIT", "WAIT", value.decision_score, ("decision_score_below_execution_floor",))
        blocked = [check for check in checks if check.status != "PASS"]
        if blocked:
            return ExecutionReadinessDecision("EXECUTION_BLOCKED", "WAIT", self._score(checks), tuple(reason for check in blocked for reason in check.reasons))
        readiness_score = self._score(checks)
        if readiness_score < self.minimum_readiness_score:
            return ExecutionReadinessDecision("EXECUTION_WAIT", "WAIT", readiness_score, ("combined_readiness_score_below_floor",))
        return ExecutionReadinessDecision("EXECUTION_READY", value.action, readiness_score, ("execution_readiness_confirmed_from_data",))

    def _score(self, checks: list[ReadinessCheckResult]) -> float:
        if not checks:
            return 0.0
        return round(sum(check.score for check in checks) / len(checks), 4)
