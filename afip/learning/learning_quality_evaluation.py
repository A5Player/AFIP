"""Learning quality evaluation for AFIP Production Milestone A Pack 11."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _bounded(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class LearningQualityResult:
    """Learning quality result for optimization review."""

    quality_score: float
    sample_quality: float
    outcome_quality: float
    stability_quality: float
    status: str
    reason: str


class LearningQualityEvaluation:
    """Evaluate whether optimization input is suitable for production use."""

    def evaluate(self, metrics: Mapping[str, float]) -> LearningQualityResult:
        """Return a bounded learning quality assessment."""
        sample_count = max(0.0, float(metrics.get("sample_count", 0.0)))
        win_rate = _bounded(metrics.get("win_rate", 0.50), 0.0, 1.0)
        profit_factor = _bounded(metrics.get("profit_factor", 1.00), 0.0, 3.0)
        drawdown_ratio = _bounded(metrics.get("drawdown_ratio", 0.25), 0.0, 1.0)
        drift_ratio = _bounded(metrics.get("drift_ratio", 0.25), 0.0, 1.0)

        sample_quality = _bounded(sample_count / 240.0, 0.0, 1.0)
        outcome_quality = _bounded(win_rate * 0.55 + (profit_factor / 3.0) * 0.45, 0.0, 1.0)
        stability_quality = _bounded(1.0 - (drawdown_ratio * 0.60 + drift_ratio * 0.40), 0.0, 1.0)
        quality_score = sample_quality * 0.30 + outcome_quality * 0.40 + stability_quality * 0.30

        if quality_score >= 0.72:
            status = "OPTIMIZATION_READY"
            reason = "learning_quality_supports_parameter_optimization"
        elif quality_score >= 0.50:
            status = "OPTIMIZATION_LIMITED"
            reason = "learning_quality_supports_limited_parameter_change"
        else:
            status = "OBSERVATION_ONLY"
            reason = "learning_quality_requires_additional_market_samples"

        return LearningQualityResult(
            quality_score=round(quality_score, 4),
            sample_quality=round(sample_quality, 4),
            outcome_quality=round(outcome_quality, 4),
            stability_quality=round(stability_quality, 4),
            status=status,
            reason=reason,
        )
