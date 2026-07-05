"""Production Milestone B Pack 8 - adaptive learning loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

from .execution_feedback_record import ExecutionFeedbackRecord
from .learning_weight_update import LearningWeightUpdate
from .performance_attribution_model import PerformanceAttributionModel


@dataclass(frozen=True)
class AdaptiveLearningLoopResult:
    status: str
    learning_score: float
    updated_weights: dict[str, float]
    records_processed: int
    reason: str


class AdaptiveLearningLoop:
    """Convert closed execution feedback into bounded adaptive weight updates."""

    def __init__(self) -> None:
        self._attribution = PerformanceAttributionModel()
        self._weight_update = LearningWeightUpdate()

    def process(
        self,
        feedback_records: Iterable[ExecutionFeedbackRecord | Mapping[str, Any]],
        current_weights: Mapping[str, float] | None = None,
    ) -> AdaptiveLearningLoopResult:
        records = [
            item if isinstance(item, ExecutionFeedbackRecord) else ExecutionFeedbackRecord.from_mapping(item)
            for item in feedback_records
        ]
        weights = dict(current_weights or {"trend": 0.25, "liquidity": 0.25, "execution": 0.25, "risk": 0.25})
        attribution = self._attribution.evaluate(records)
        update = self._weight_update.update(weights, attribution.contribution_score)
        if not records:
            return AdaptiveLearningLoopResult("LEARNING_LOOP_EMPTY", 0.0, update.updated_weights, 0, "no_execution_feedback")
        status = "LEARNING_LOOP_READY" if attribution.status == "ATTRIBUTION_POSITIVE" else "LEARNING_LOOP_REVIEW"
        return AdaptiveLearningLoopResult(status, attribution.contribution_score, update.updated_weights, len(records), attribution.reason)
