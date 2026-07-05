from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionActionResult:
    status: str
    action: str
    execution_status: str
    reason: str


class DecisionAction:
    """Convert unified direction, confidence, consensus, and risk into an execution action."""

    VALID_DIRECTIONS = {"BUY", "SELL", "FLAT", "WAIT", "NO_ACTION"}

    def select(
        self,
        direction: str = "FLAT",
        confidence: float = 0.0,
        consensus_level: str = "LOW",
        risk_accepted: bool = True,
        execution_quality: str = "ACCEPTABLE",
    ) -> DecisionActionResult:
        selected_direction = str(direction or "FLAT").upper()
        if selected_direction not in self.VALID_DIRECTIONS:
            selected_direction = "FLAT"
        selected_consensus = str(consensus_level or "LOW").upper()
        selected_execution = str(execution_quality or "ACCEPTABLE").upper()
        score = self._normalize_score(confidence)

        if not risk_accepted:
            return DecisionActionResult("DECISION_ACTION_READY", "NO_ACTION", "RISK_REDUCED", "risk_not_accepted")
        if selected_direction in {"FLAT", "WAIT", "NO_ACTION"}:
            return DecisionActionResult("DECISION_ACTION_READY", "WAIT", "REVIEW", "direction_requires_wait")
        if selected_execution in {"REDUCED", "CAUTION"} and score < 0.82:
            return DecisionActionResult("DECISION_ACTION_READY", "REDUCE", "SELECTIVE", "execution_quality_requires_reduction")
        if selected_consensus == "HIGH" and score >= 0.72:
            return DecisionActionResult("DECISION_ACTION_READY", selected_direction, "ACCEPTABLE", "unified_decision_accepted")
        if selected_consensus == "MODERATE" and score >= 0.80:
            return DecisionActionResult("DECISION_ACTION_READY", selected_direction, "SELECTIVE", "decision_accepted_with_selective_execution")
        return DecisionActionResult("DECISION_ACTION_READY", "WAIT", "REVIEW", "decision_threshold_not_met")

    @staticmethod
    def _normalize_score(value: float) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        if score > 1.0:
            score = score / 100.0
        return max(0.0, min(score, 1.0))
