"""Market context transition model for AFIP Production Milestone B."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextTransitionResult:
    """Transition assessment between previous and current market context."""

    status: str
    transition_state: str
    stability_score: float
    reason: str


class ContextTransitionModel:
    """Evaluates whether the current market context is stable or shifting."""

    def evaluate(self, previous_state: str | None, current_state: str | None) -> ContextTransitionResult:
        previous = (previous_state or "NEUTRAL").upper()
        current = (current_state or "NEUTRAL").upper()

        if previous == current:
            transition = "STABLE_CONTEXT"
            stability = 92.0
            status = "CONTEXT_TRANSITION_READY"
        elif previous == "NEUTRAL" or current == "NEUTRAL":
            transition = "MODERATE_CONTEXT_TRANSITION"
            stability = 68.0
            status = "CONTEXT_TRANSITION_READY"
        else:
            transition = "ACTIVE_CONTEXT_TRANSITION"
            stability = 54.0
            status = "CONTEXT_TRANSITION_REVIEW"

        return ContextTransitionResult(
            status=status,
            transition_state=transition,
            stability_score=stability,
            reason=f"context_transition_{previous.lower()}_to_{current.lower()}",
        )
