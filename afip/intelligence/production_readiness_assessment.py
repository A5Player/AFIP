"""Production readiness assessment for AFIP Production Milestone A Pack 12."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for deterministic financial assessment."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class ProductionReadinessResult:
    """Readiness score for production-oriented adaptive intelligence."""

    readiness_score: float
    status: str
    action: str
    reason: str


class ProductionReadinessAssessment:
    """Assess whether runtime inputs are ready for controlled production use."""

    def assess(self, metrics: Mapping[str, float]) -> ProductionReadinessResult:
        """Return a stable production readiness assessment."""
        decision_quality = _ratio(metrics.get("decision_quality", 0.50))
        optimization_quality = _ratio(metrics.get("optimization_quality", 0.50))
        execution_quality = _ratio(metrics.get("execution_quality", 0.50))
        portfolio_quality = _ratio(metrics.get("portfolio_quality", 0.50))
        data_completeness = _ratio(metrics.get("data_completeness", 0.50))
        drawdown_pressure = _ratio(metrics.get("drawdown_pressure", 0.50))

        quality_score = (
            decision_quality * 0.24
            + optimization_quality * 0.20
            + execution_quality * 0.20
            + portfolio_quality * 0.18
            + data_completeness * 0.18
        )
        readiness_score = _ratio(quality_score * (1.0 - drawdown_pressure * 0.35))

        if readiness_score >= 0.78 and drawdown_pressure <= 0.35:
            status = "PRODUCTION_READY"
            action = "ENABLE_CONTROLLED_PRODUCTION_MODE"
            reason = "readiness_score_supports_controlled_production"
        elif readiness_score >= 0.58:
            status = "PRODUCTION_CANDIDATE"
            action = "KEEP_SIMULATION_WITH_PRODUCTION_REVIEW"
            reason = "readiness_score_requires_additional_validation"
        else:
            status = "SIMULATION_ONLY"
            action = "KEEP_SIMULATION_ONLY"
            reason = "readiness_score_below_production_threshold"

        return ProductionReadinessResult(
            readiness_score=round(readiness_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
