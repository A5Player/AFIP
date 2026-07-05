"""Production Milestone B Pack 8 - learning weight update."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class LearningWeightUpdateResult:
    status: str
    updated_weights: dict[str, float]
    adjustment_score: float
    reason: str


class LearningWeightUpdate:
    """Apply bounded adaptive weight updates from performance feedback."""

    def update(
        self,
        current_weights: Mapping[str, float],
        performance_score: float,
        learning_rate: float = 0.05,
    ) -> LearningWeightUpdateResult:
        if not current_weights:
            return LearningWeightUpdateResult("WEIGHT_UPDATE_EMPTY", {}, 0.0, "no_weight_profile")

        bounded_rate = min(0.20, max(0.0, float(learning_rate)))
        score = min(100.0, max(0.0, float(performance_score)))
        adjustment = ((score - 50.0) / 50.0) * bounded_rate
        raw = {str(key): max(0.0, float(value) * (1.0 + adjustment)) for key, value in current_weights.items()}
        total = sum(raw.values()) or 1.0
        normalized = {key: round(value / total, 6) for key, value in raw.items()}
        drift = round(abs(adjustment) * 100.0, 4)
        status = "WEIGHT_UPDATE_READY" if drift <= 20.0 else "WEIGHT_UPDATE_REVIEW"
        return LearningWeightUpdateResult(status, normalized, drift, "bounded_learning_weight_update")
