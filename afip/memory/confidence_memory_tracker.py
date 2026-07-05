"""Production Milestone B Pack 9 - confidence memory tracker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any


@dataclass(frozen=True)
class ConfidenceMemoryTrackerResult:
    status: str
    current_confidence: float
    average_confidence: float
    confidence_change: float
    stability_score: float
    reason: str


class ConfidenceMemoryTracker:
    """Track confidence continuity across recent decision observations."""

    def evaluate(self, confidence_values: Iterable[Any]) -> ConfidenceMemoryTrackerResult:
        values = [_bounded_score(value) for value in confidence_values]
        if not values:
            return ConfidenceMemoryTrackerResult("CONFIDENCE_MEMORY_EMPTY", 0.0, 0.0, 0.0, 0.0, "no_confidence_memory")
        current = values[-1]
        average = round(sum(values) / len(values), 4)
        change = round(current - values[0], 4)
        variance_proxy = sum(abs(value - average) for value in values) / len(values)
        stability = round(max(0.0, 100.0 - variance_proxy), 2)
        status = "CONFIDENCE_MEMORY_READY" if stability >= 70.0 and average >= 50.0 else "CONFIDENCE_MEMORY_REVIEW"
        reason = "confidence_memory_stable" if status == "CONFIDENCE_MEMORY_READY" else "confidence_memory_review"
        return ConfidenceMemoryTrackerResult(status, current, average, change, stability, reason)


def _bounded_score(value: Any) -> float:
    numeric = float(value)
    if numeric <= 1.0:
        numeric *= 100.0
    return round(min(100.0, max(0.0, numeric)), 4)
