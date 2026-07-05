from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.decision.decision_action import DecisionAction
from afip.decision.decision_confidence import DecisionConfidence
from afip.decision.decision_reasoning import DecisionReasoning


@dataclass(frozen=True)
class UnifiedDecisionResult:
    status: str
    action: str
    direction: str
    confidence: float
    confidence_level: str
    consensus_level: str
    risk_status: str
    execution_status: str
    reason: str
    explanation: str


class UnifiedDecisionEngine:
    """Create a single production decision from fusion, weighting, conflict, and risk profiles."""

    def decide(
        self,
        fusion_profile: Mapping[str, object] | None = None,
        weight_profile: Mapping[str, object] | None = None,
        conflict_profile: Mapping[str, object] | None = None,
        risk_profile: Mapping[str, object] | None = None,
        supporting_factors: Iterable[str] | None = None,
    ) -> UnifiedDecisionResult:
        fusion = dict(fusion_profile or {})
        weight = dict(weight_profile or {})
        conflict = dict(conflict_profile or {})
        risk = dict(risk_profile or {})

        direction = self._direction(
            conflict.get("reconciled_direction", conflict.get("action", fusion.get("direction", fusion.get("action", "FLAT"))))
        )
        fusion_score = self._value(fusion.get("confidence", fusion.get("score", 0.0)))
        adaptive_score = self._value(weight.get("adaptive_score", weight.get("score", fusion_score)))
        consensus_score = self._value(conflict.get("consensus_score", conflict.get("confidence", fusion_score)))
        conflict_ratio = self._value(conflict.get("conflict_ratio", 0.0))
        consensus_level = str(conflict.get("consensus_level", "LOW")).upper()
        risk_accepted = self._risk_accepted(risk)
        execution_quality = str(risk.get("execution_quality", risk.get("status", "ACCEPTABLE"))).upper()

        confidence = DecisionConfidence().calculate(
            fusion_score=fusion_score,
            adaptive_weight_score=adaptive_score,
            consensus_score=consensus_score,
            conflict_ratio=conflict_ratio,
            risk_accepted=risk_accepted,
        )
        action = DecisionAction().select(
            direction=direction,
            confidence=confidence.confidence,
            consensus_level=consensus_level,
            risk_accepted=risk_accepted,
            execution_quality=execution_quality,
        )
        reasoning = DecisionReasoning().explain(
            action=action.action,
            direction=direction,
            consensus_level=consensus_level,
            confidence_level=confidence.confidence_level,
            factors=supporting_factors,
            risk_accepted=risk_accepted,
        )

        return UnifiedDecisionResult(
            status="UNIFIED_DECISION_READY",
            action=action.action,
            direction=direction,
            confidence=confidence.confidence,
            confidence_level=confidence.confidence_level,
            consensus_level=consensus_level,
            risk_status="ACCEPTED" if risk_accepted else "NOT_ACCEPTED",
            execution_status=action.execution_status,
            reason=reasoning.primary_reason,
            explanation=reasoning.explanation,
        )

    @staticmethod
    def _value(value: object) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))

    @staticmethod
    def _direction(value: object) -> str:
        direction = str(value or "FLAT").upper()
        return direction if direction in {"BUY", "SELL", "FLAT", "WAIT", "NO_ACTION"} else "FLAT"

    @staticmethod
    def _risk_accepted(profile: Mapping[str, object]) -> bool:
        if not profile:
            return True
        if "risk_accepted" in profile:
            return bool(profile.get("risk_accepted"))
        if "allowed" in profile:
            return bool(profile.get("allowed"))
        status = str(profile.get("status", "ACCEPTABLE")).upper()
        return status not in {"REJECTED", "BLOCKED", "NOT_ACCEPTED"}
