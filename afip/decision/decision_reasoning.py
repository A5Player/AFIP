from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DecisionReasoningResult:
    status: str
    primary_reason: str
    explanation: str
    supporting_factors: tuple[str, ...]


class DecisionReasoning:
    """Build concise financial reasoning for a unified decision result."""

    def explain(
        self,
        action: str = "WAIT",
        direction: str = "FLAT",
        consensus_level: str = "LOW",
        confidence_level: str = "LOW",
        factors: Iterable[str] | None = None,
        risk_accepted: bool = True,
    ) -> DecisionReasoningResult:
        selected_action = str(action or "WAIT").upper()
        selected_direction = str(direction or "FLAT").upper()
        selected_consensus = str(consensus_level or "LOW").upper()
        selected_confidence = str(confidence_level or "LOW").upper()
        factor_tuple = tuple(str(item).lower() for item in (factors or []) if str(item).strip())

        if not risk_accepted:
            primary = "risk_not_accepted"
        elif selected_action in {"BUY", "SELL"}:
            primary = "unified_direction_accepted"
        elif selected_action == "REDUCE":
            primary = "selective_exposure_reduction"
        else:
            primary = "decision_wait_for_confirmation"

        explanation = (
            f"{selected_action} because direction={selected_direction}, "
            f"consensus={selected_consensus}, confidence={selected_confidence}, "
            f"risk={'ACCEPTED' if risk_accepted else 'NOT_ACCEPTED'}"
        )
        if factor_tuple:
            explanation = f"{explanation}, factors={'+'.join(factor_tuple)}"

        return DecisionReasoningResult(
            status="DECISION_REASONING_READY",
            primary_reason=primary,
            explanation=explanation,
            supporting_factors=factor_tuple,
        )
