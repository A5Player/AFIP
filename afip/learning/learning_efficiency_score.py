"""Production Milestone A Pack 8: learning efficiency score."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class LearningEfficiencyScoreResult:
    """Learning efficiency result for production optimization cycles."""

    status: str
    optimization_allowed: bool
    efficiency_score: float
    efficiency_state: str
    sample_count: int
    positive_ratio: float
    calibration_quality: float
    stability_quality: float
    blockers: list[str] = field(default_factory=list)
    reason: str = "learning_efficiency_score_evaluated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "optimization_allowed": self.optimization_allowed,
            "efficiency_score": round(self.efficiency_score, 2),
            "efficiency_state": self.efficiency_state,
            "sample_count": self.sample_count,
            "positive_ratio": round(self.positive_ratio, 4),
            "calibration_quality": round(self.calibration_quality, 2),
            "stability_quality": round(self.stability_quality, 2),
            "blockers": list(self.blockers),
            "reason": self.reason,
        }


class LearningEfficiencyScore:
    """Evaluate whether learning samples are efficient enough for optimization."""

    def evaluate(self, samples: Iterable[Mapping[str, Any]]) -> LearningEfficiencyScoreResult:
        sample_list = list(samples)
        sample_count = len(sample_list)
        positive_count = 0
        total_alignment = 0.0
        total_stability = 0.0

        for sample in sample_list:
            net_points = _numeric(sample.get("net_points", 0.0))
            if str(sample.get("outcome", "")).upper() == "WIN" or net_points > 0.0:
                positive_count += 1
            entry_score = _bounded(sample.get("entry_score", 50.0))
            position_confidence = _bounded(sample.get("position_confidence", 50.0))
            total_alignment += 100.0 - abs(entry_score - position_confidence)
            total_stability += _bounded(sample.get("stability_score", sample.get("confidence", position_confidence)))

        positive_ratio = positive_count / sample_count if sample_count else 0.0
        calibration_quality = total_alignment / sample_count if sample_count else 0.0
        stability_quality = total_stability / sample_count if sample_count else 0.0
        sample_depth_quality = min(100.0, sample_count / 8.0 * 100.0)
        positive_quality = positive_ratio * 100.0
        efficiency_score = (
            sample_depth_quality * 0.25
            + positive_quality * 0.25
            + calibration_quality * 0.25
            + stability_quality * 0.25
        )

        blockers: list[str] = []
        if sample_count < 5:
            blockers.append("learning_sample_count_below_efficiency_threshold")
        if positive_ratio < 0.45:
            blockers.append("positive_learning_ratio_below_efficiency_threshold")
        if calibration_quality < 55.0:
            blockers.append("learning_calibration_quality_below_efficiency_threshold")
        if stability_quality < 50.0:
            blockers.append("learning_stability_quality_below_efficiency_threshold")

        optimization_allowed = efficiency_score >= 60.0 and not blockers
        if efficiency_score >= 82.0:
            efficiency_state = "HIGH_EFFICIENCY"
        elif efficiency_score >= 60.0:
            efficiency_state = "STANDARD_EFFICIENCY"
        else:
            efficiency_state = "LOW_EFFICIENCY"

        return LearningEfficiencyScoreResult(
            status="READY" if optimization_allowed else "OBSERVE",
            optimization_allowed=optimization_allowed,
            efficiency_score=efficiency_score,
            efficiency_state=efficiency_state,
            sample_count=sample_count,
            positive_ratio=positive_ratio,
            calibration_quality=calibration_quality,
            stability_quality=stability_quality,
            blockers=blockers,
            reason="learning_efficiency_ready" if optimization_allowed else "learning_efficiency_observation_required",
        )


def _numeric(value: Any) -> float:
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
