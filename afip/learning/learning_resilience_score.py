"""Production Milestone A Pack 9: learning resilience score."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class LearningResilienceScoreResult:
    """Learning resilience result for optimization safety."""

    status: str
    optimization_allowed: bool
    resilience_score: float
    resilience_state: str
    positive_ratio: float
    average_points: float
    sample_consistency: float
    confidence_quality: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "learning_resilience_score_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "optimization_allowed": self.optimization_allowed,
            "resilience_score": round(self.resilience_score, 2),
            "resilience_state": self.resilience_state,
            "positive_ratio": round(self.positive_ratio, 2),
            "average_points": round(self.average_points, 2),
            "sample_consistency": round(self.sample_consistency, 2),
            "confidence_quality": round(self.confidence_quality, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class LearningResilienceScore:
    """Evaluate whether learning evidence remains resilient across recent samples."""

    def evaluate(self, samples: Iterable[Mapping[str, Any]]) -> LearningResilienceScoreResult:
        rows = list(samples)
        if not rows:
            return LearningResilienceScoreResult(
                status="OBSERVE",
                optimization_allowed=False,
                resilience_score=0.0,
                resilience_state="INSUFFICIENT_EVIDENCE",
                positive_ratio=0.0,
                average_points=0.0,
                sample_consistency=0.0,
                confidence_quality=0.0,
                blockers=["learning_samples_missing_for_resilience_score"],
                reason="learning_resilience_requires_samples",
            )

        point_values = [_float(row.get("net_points", 0.0)) for row in rows]
        positive_count = sum(1 for value in point_values if value > 0.0)
        positive_ratio = positive_count / len(rows) * 100.0
        average_points = sum(point_values) / len(rows)
        losses = sum(1 for value in point_values if value <= 0.0)
        sample_consistency = max(0.0, 100.0 - losses / len(rows) * 100.0)
        confidence_values = [_bounded(row.get("confidence", row.get("position_confidence", 50.0))) for row in rows]
        confidence_quality = sum(confidence_values) / len(confidence_values)

        points_quality = max(0.0, min(100.0, 50.0 + average_points / 4.0))
        resilience_score = (
            positive_ratio * 0.30
            + points_quality * 0.25
            + sample_consistency * 0.20
            + confidence_quality * 0.25
        )

        blockers: list[str] = []
        if len(rows) < 5:
            blockers.append("learning_sample_count_below_resilience_threshold")
        if positive_ratio < 55.0:
            blockers.append("positive_ratio_below_learning_resilience_threshold")
        if average_points <= 0.0:
            blockers.append("average_points_below_learning_resilience_threshold")
        if confidence_quality < 55.0:
            blockers.append("confidence_quality_below_learning_resilience_threshold")

        optimization_allowed = resilience_score >= 60.0 and not blockers
        if resilience_score >= 82.0:
            resilience_state = "HIGH_RESILIENCE"
        elif resilience_score >= 60.0:
            resilience_state = "STANDARD_RESILIENCE"
        else:
            resilience_state = "LOW_RESILIENCE"

        return LearningResilienceScoreResult(
            status="READY" if optimization_allowed else "OBSERVE",
            optimization_allowed=optimization_allowed,
            resilience_score=resilience_score,
            resilience_state=resilience_state,
            positive_ratio=positive_ratio,
            average_points=average_points,
            sample_consistency=sample_consistency,
            confidence_quality=confidence_quality,
            blockers=blockers,
            reason="learning_resilience_ready" if optimization_allowed else "learning_resilience_observation_required",
        )


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bounded(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 50.0
    return max(0.0, min(100.0, numeric))
