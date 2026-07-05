"""Adaptive integration summary for AFIP Production Milestone A Pack 12."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for adaptive integration summary."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class AdaptiveIntegrationResult:
    """Summary of adaptive intelligence integration quality."""

    integration_score: float
    status: str
    action: str
    reason: str


class AdaptiveIntegrationSummary:
    """Summarize adaptive intelligence quality across Milestone A layers."""

    def summarize(self, metrics: Mapping[str, float]) -> AdaptiveIntegrationResult:
        """Return integration quality without changing existing runtime behavior."""
        readiness_score = _ratio(metrics.get("readiness_score", 0.50))
        runtime_health_score = _ratio(metrics.get("runtime_health_score", 0.50))
        portfolio_quality_score = _ratio(metrics.get("portfolio_quality_score", 0.50))
        learning_quality_score = _ratio(metrics.get("learning_quality_score", 0.50))
        compatibility_score = _ratio(metrics.get("compatibility_score", 1.00))

        integration_score = _ratio(
            readiness_score * 0.24
            + runtime_health_score * 0.22
            + portfolio_quality_score * 0.20
            + learning_quality_score * 0.20
            + compatibility_score * 0.14
        )

        if integration_score >= 0.80 and compatibility_score >= 0.95:
            status = "MILESTONE_A_READY"
            action = "PREPARE_MILESTONE_A_RELEASE"
            reason = "adaptive_integration_supports_milestone_release"
        elif integration_score >= 0.62:
            status = "MILESTONE_A_STABLE"
            action = "CONTINUE_PRODUCTION_VALIDATION"
            reason = "adaptive_integration_requires_final_validation"
        else:
            status = "MILESTONE_A_REVIEW"
            action = "REVIEW_ADAPTIVE_INTEGRATION"
            reason = "adaptive_integration_below_release_threshold"

        return AdaptiveIntegrationResult(
            integration_score=round(integration_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
