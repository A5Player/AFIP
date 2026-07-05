"""Release quality assessment for AFIP Production Milestone A Pack 13."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for deterministic financial assessment."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class ReleaseQualityResult:
    """Release quality score for a production-oriented financial runtime."""

    quality_score: float
    status: str
    action: str
    reason: str


class ReleaseQualityAssessment:
    """Assess release quality using validation, documentation, and runtime evidence."""

    def assess(self, metrics: Mapping[str, float]) -> ReleaseQualityResult:
        """Return a stable release quality assessment."""
        validation_quality = _ratio(metrics.get("validation_quality", 0.50))
        documentation_quality = _ratio(metrics.get("documentation_quality", 0.50))
        runtime_quality = _ratio(metrics.get("runtime_quality", 0.50))
        compatibility_quality = _ratio(metrics.get("compatibility_quality", 0.50))
        naming_quality = _ratio(metrics.get("naming_quality", 0.50))
        regression_pressure = _ratio(metrics.get("regression_pressure", 0.50))

        raw_quality = (
            validation_quality * 0.24
            + documentation_quality * 0.16
            + runtime_quality * 0.22
            + compatibility_quality * 0.22
            + naming_quality * 0.16
        )
        quality_score = _ratio(raw_quality * (1.0 - regression_pressure * 0.30))

        if quality_score >= 0.82 and regression_pressure <= 0.20:
            status = "RELEASE_QUALITY_READY"
            action = "PREPARE_MILESTONE_A_RELEASE"
            reason = "release_quality_supports_production_acceptance"
        elif quality_score >= 0.64:
            status = "RELEASE_QUALITY_REVIEW"
            action = "CONTINUE_RELEASE_VALIDATION"
            reason = "release_quality_requires_additional_validation"
        else:
            status = "RELEASE_QUALITY_NOT_READY"
            action = "KEEP_SIMULATION_ONLY"
            reason = "release_quality_below_acceptance_threshold"

        return ReleaseQualityResult(
            quality_score=round(quality_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
