"""Production Milestone A Pack 7: learning confidence interval.

Additive learning confidence evaluation for production optimization decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class LearningConfidenceIntervalResult:
    """Learning confidence interval result for adaptive optimization."""

    status: str
    confidence_interval_score: float
    sample_depth_score: float
    outcome_consistency_score: float
    optimization_confidence_score: float
    confidence_state: str
    optimization_allowed: bool
    blockers: list[str] = field(default_factory=list)
    reason: str = "learning_confidence_interval_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "confidence_interval_score": round(self.confidence_interval_score, 2),
            "sample_depth_score": round(self.sample_depth_score, 2),
            "outcome_consistency_score": round(self.outcome_consistency_score, 2),
            "optimization_confidence_score": round(self.optimization_confidence_score, 2),
            "confidence_state": self.confidence_state,
            "optimization_allowed": self.optimization_allowed,
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class LearningConfidenceInterval:
    """Evaluates whether learning samples are reliable enough for optimization."""

    def evaluate(self, samples: Iterable[Mapping[str, Any]]) -> LearningConfidenceIntervalResult:
        rows = list(samples)
        sample_count = len(rows)
        if sample_count == 0:
            return LearningConfidenceIntervalResult(
                status="OBSERVE",
                confidence_interval_score=0.0,
                sample_depth_score=0.0,
                outcome_consistency_score=0.0,
                optimization_confidence_score=0.0,
                confidence_state="INSUFFICIENT_DATA",
                optimization_allowed=False,
                blockers=["learning_samples_missing"],
                reason="learning_confidence_interval_missing_samples",
            )

        wins = sum(1 for row in rows if str(row.get("outcome", "")).upper() == "WIN")
        win_rate = wins / sample_count
        points = [float(row.get("net_points", 0.0)) for row in rows]
        average_points = sum(points) / sample_count
        dispersion = sum(abs(point - average_points) for point in points) / sample_count

        sample_depth_score = _clamp(sample_count * 8.0)
        outcome_consistency_score = _clamp(100.0 - abs(win_rate - 0.62) * 85.0 - min(30.0, dispersion / 18.0))
        optimization_confidence_score = _clamp(55.0 + average_points / 6.0 + win_rate * 25.0)
        confidence_interval_score = (sample_depth_score * 0.30) + (outcome_consistency_score * 0.35) + (optimization_confidence_score * 0.35)

        blockers: list[str] = []
        if sample_count < 5:
            blockers.append("learning_sample_depth_below_production_threshold")
        if outcome_consistency_score < 52.0:
            blockers.append("learning_outcome_consistency_low")
        if optimization_confidence_score < 58.0:
            blockers.append("learning_optimization_confidence_low")
        if confidence_interval_score < 62.0:
            blockers.append("learning_confidence_interval_score_low")

        if confidence_interval_score >= 80.0 and not blockers:
            confidence_state = "HIGH_CONFIDENCE"
        elif confidence_interval_score >= 66.0 and not blockers:
            confidence_state = "STANDARD_CONFIDENCE"
        else:
            confidence_state = "LIMITED_CONFIDENCE"

        optimization_allowed = not blockers and confidence_interval_score >= 66.0
        return LearningConfidenceIntervalResult(
            status="READY" if optimization_allowed else "OBSERVE",
            confidence_interval_score=confidence_interval_score,
            sample_depth_score=sample_depth_score,
            outcome_consistency_score=outcome_consistency_score,
            optimization_confidence_score=optimization_confidence_score,
            confidence_state=confidence_state,
            optimization_allowed=optimization_allowed,
            blockers=blockers,
            reason="learning_confidence_interval_ready" if optimization_allowed else "learning_confidence_interval_observation_required",
        )
