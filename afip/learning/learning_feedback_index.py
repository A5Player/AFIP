"""Production Milestone A Pack 5: learning feedback index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class LearningFeedbackIndexResult:
    """Aggregated feedback quality for adaptive learning decisions."""

    status: str
    feedback_score: float
    sample_count: int
    positive_ratio: float
    average_return_points: float
    optimization_bias: str
    blockers: list[str] = field(default_factory=list)
    reason: str = "learning_feedback_index_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "feedback_score": round(self.feedback_score, 2),
            "sample_count": self.sample_count,
            "positive_ratio": round(self.positive_ratio, 2),
            "average_return_points": round(self.average_return_points, 2),
            "optimization_bias": self.optimization_bias,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class LearningFeedbackIndex:
    """Converts recent trade feedback into a bounded optimization signal."""

    def __init__(self, minimum_samples: int = 5) -> None:
        self.minimum_samples = int(minimum_samples)

    def evaluate(self, samples: Iterable[Mapping[str, Any]]) -> LearningFeedbackIndexResult:
        rows = list(samples)
        sample_count = len(rows)
        if sample_count == 0:
            return LearningFeedbackIndexResult("OBSERVE", 0.0, 0, 0.0, 0.0, "NEUTRAL", ["no_learning_feedback"], "learning_feedback_waiting_for_samples")

        returns = [float(row.get("net_points", row.get("return_points", 0.0))) for row in rows]
        positive = sum(1 for value in returns if value > 0.0)
        positive_ratio = positive / sample_count * 100.0
        average_return = sum(returns) / sample_count
        return_quality = max(0.0, min(100.0, 50.0 + average_return / 4.0))
        feedback_score = (positive_ratio * 0.60) + (return_quality * 0.40)

        blockers: list[str] = []
        if sample_count < self.minimum_samples:
            blockers.append("insufficient_learning_feedback")
        if positive_ratio < 45.0:
            blockers.append("low_positive_feedback_ratio")
        if feedback_score < 50.0:
            blockers.append("low_feedback_score")

        if feedback_score >= 70.0 and average_return > 0.0:
            optimization_bias = "POSITIVE"
        elif feedback_score < 50.0 or average_return < 0.0:
            optimization_bias = "DEFENSIVE"
        else:
            optimization_bias = "NEUTRAL"

        return LearningFeedbackIndexResult(
            status="READY" if not blockers else "OBSERVE",
            feedback_score=feedback_score,
            sample_count=sample_count,
            positive_ratio=positive_ratio,
            average_return_points=average_return,
            optimization_bias=optimization_bias,
            blockers=blockers,
            reason="learning_feedback_index_ready" if not blockers else "learning_feedback_index_protective_observation",
        )
