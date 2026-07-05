"""Conflict resolution for AFIP financial intelligence fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class IntelligenceConflictResolutionResult:
    """Financial signal conflict resolution result."""

    status: str
    action: str
    conflict_score: float
    resolved_direction: str
    reason: str


class IntelligenceConflictResolution:
    """Resolve directional conflict without using simple majority voting."""

    def resolve(self, signals: Iterable[Mapping[str, float | str]]) -> IntelligenceConflictResolutionResult:
        """Return a conflict-aware financial direction."""
        direction_strength = {"BUY": 0.0, "SELL": 0.0, "FLAT": 0.0}
        total_strength = 0.0

        for signal in signals:
            direction = str(signal.get("direction", "FLAT")).upper()
            if direction not in direction_strength:
                direction = "FLAT"
            confidence = self._ratio(float(signal.get("confidence", 0.0)))
            priority = self._ratio(float(signal.get("priority", 1.0)))
            strength = confidence * max(priority, 0.05)
            direction_strength[direction] += strength
            total_strength += strength

        if total_strength <= 0.0:
            return IntelligenceConflictResolutionResult(
                status="CONFLICT_INPUT_EMPTY",
                action="KEEP_SIMULATION_ONLY",
                conflict_score=100.0,
                resolved_direction="FLAT",
                reason="no_financial_conflict_input",
            )

        ranked = sorted(direction_strength.items(), key=lambda item: item[1], reverse=True)
        top_direction, top_strength = ranked[0]
        second_strength = ranked[1][1]
        conflict_score = round((second_strength / max(top_strength, 0.0001)) * 100.0, 2)

        if conflict_score <= 55.0 and top_direction != "FLAT":
            status = "CONFLICT_RESOLVED"
            action = "ACCEPT_RESOLVED_FINANCIAL_DIRECTION"
            resolved_direction = top_direction
            reason = "dominant_priority_adjusted_direction"
        elif conflict_score <= 80.0:
            status = "CONFLICT_REVIEW"
            action = "REVIEW_FINANCIAL_DIRECTION"
            resolved_direction = "FLAT"
            reason = "directional_conflict_requires_review"
        else:
            status = "CONFLICT_HIGH"
            action = "KEEP_SIMULATION_ONLY"
            resolved_direction = "FLAT"
            reason = "directional_conflict_above_threshold"

        return IntelligenceConflictResolutionResult(
            status=status,
            action=action,
            conflict_score=conflict_score,
            resolved_direction=resolved_direction,
            reason=reason,
        )

    @staticmethod
    def _ratio(value: float) -> float:
        """Normalize score to a zero-to-one range."""
        if value > 1.0:
            value = value / 100.0
        return min(max(value, 0.0), 1.0)
