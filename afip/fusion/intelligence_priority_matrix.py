"""Priority matrix for AFIP financial intelligence fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class IntelligencePriorityMatrixResult:
    """Priority matrix evaluation result."""

    status: str
    action: str
    priority_score: float
    dominant_component: str
    reason: str


class IntelligencePriorityMatrix:
    """Evaluate priority across market, risk, execution, and portfolio components."""

    _WEIGHTS = {
        "market": 0.25,
        "risk": 0.25,
        "execution": 0.20,
        "portfolio": 0.18,
        "learning": 0.12,
    }

    def evaluate(self, metrics: Mapping[str, float]) -> IntelligencePriorityMatrixResult:
        """Return a weighted priority score for production financial decision flow."""
        weighted_score = 0.0
        component_scores: dict[str, float] = {}
        for component, weight in self._WEIGHTS.items():
            score = self._ratio(float(metrics.get(component, 0.0)))
            component_scores[component] = score
            weighted_score += score * weight

        priority_score = round(weighted_score * 100.0, 2)
        dominant_component = max(component_scores, key=component_scores.get)

        if priority_score >= 78.0:
            status = "PRIORITY_MATRIX_READY"
            action = "ACCEPT_PRIORITY_ALLOCATION"
            reason = "financial_priority_inputs_aligned"
        elif priority_score >= 58.0:
            status = "PRIORITY_MATRIX_REVIEW"
            action = "REVIEW_PRIORITY_ALLOCATION"
            reason = "financial_priority_inputs_mixed"
        else:
            status = "PRIORITY_MATRIX_NOT_READY"
            action = "KEEP_SIMULATION_ONLY"
            reason = "financial_priority_inputs_insufficient"

        return IntelligencePriorityMatrixResult(
            status=status,
            action=action,
            priority_score=priority_score,
            dominant_component=dominant_component.upper(),
            reason=reason,
        )

    @staticmethod
    def _ratio(value: float) -> float:
        """Normalize score to a zero-to-one range."""
        if value > 1.0:
            value = value / 100.0
        return min(max(value, 0.0), 1.0)
