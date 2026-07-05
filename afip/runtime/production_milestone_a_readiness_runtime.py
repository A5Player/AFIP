"""Production readiness runtime for AFIP Production Milestone A Pack 12."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.intelligence.portfolio_quality_assessment import PortfolioQualityAssessment, PortfolioQualityResult
from afip.intelligence.production_readiness_assessment import ProductionReadinessAssessment, ProductionReadinessResult
from afip.intelligence.runtime_health_assessment import RuntimeHealthAssessment, RuntimeHealthResult
from afip.learning.adaptive_integration_summary import AdaptiveIntegrationResult, AdaptiveIntegrationSummary


@dataclass(frozen=True)
class ProductionReadinessRuntimeResult:
    """Integrated Pack 12 readiness runtime output."""

    status: str
    action: str
    production_readiness: ProductionReadinessResult
    runtime_health: RuntimeHealthResult
    portfolio_quality: PortfolioQualityResult
    adaptive_integration: AdaptiveIntegrationResult
    reason: str


class ProductionMilestoneAReadinessRuntime:
    """Integrate readiness, runtime health, portfolio quality, and adaptive summary."""

    def __init__(self) -> None:
        self._production_readiness = ProductionReadinessAssessment()
        self._runtime_health = RuntimeHealthAssessment()
        self._portfolio_quality = PortfolioQualityAssessment()
        self._adaptive_summary = AdaptiveIntegrationSummary()

    def evaluate(
        self,
        readiness_metrics: Mapping[str, float],
        runtime_metrics: Mapping[str, float],
        portfolio_metrics: Mapping[str, float],
        learning_metrics: Mapping[str, float],
    ) -> ProductionReadinessRuntimeResult:
        """Return a production readiness decision that preserves simulation safety."""
        runtime_health = self._runtime_health.assess(runtime_metrics)
        portfolio_quality = self._portfolio_quality.assess(portfolio_metrics)

        merged_readiness_metrics = dict(readiness_metrics)
        merged_readiness_metrics["portfolio_quality"] = portfolio_quality.quality_score
        production_readiness = self._production_readiness.assess(merged_readiness_metrics)

        adaptive_integration = self._adaptive_summary.summarize(
            {
                "readiness_score": production_readiness.readiness_score,
                "runtime_health_score": runtime_health.health_score,
                "portfolio_quality_score": portfolio_quality.quality_score,
                "learning_quality_score": float(learning_metrics.get("learning_quality_score", 0.50)),
                "compatibility_score": float(learning_metrics.get("compatibility_score", 1.00)),
            }
        )

        if (
            production_readiness.status == "PRODUCTION_READY"
            and runtime_health.status == "RUNTIME_HEALTHY"
            and portfolio_quality.status == "PORTFOLIO_QUALITY_READY"
            and adaptive_integration.status == "MILESTONE_A_READY"
        ):
            status = "MILESTONE_A_PRODUCTION_READY"
            action = "PREPARE_CONTROLLED_PRODUCTION_RELEASE"
            reason = "all_readiness_layers_support_controlled_production_release"
        elif adaptive_integration.status == "MILESTONE_A_REVIEW" or runtime_health.status == "RUNTIME_REVIEW_REQUIRED":
            status = "MILESTONE_A_REVIEW_REQUIRED"
            action = "KEEP_SIMULATION_ONLY"
            reason = "readiness_layers_require_review_before_release"
        else:
            status = "MILESTONE_A_VALIDATION_READY"
            action = "CONTINUE_FINAL_VALIDATION"
            reason = "readiness_layers_are_stable_for_final_validation"

        return ProductionReadinessRuntimeResult(
            status=status,
            action=action,
            production_readiness=production_readiness,
            runtime_health=runtime_health,
            portfolio_quality=portfolio_quality,
            adaptive_integration=adaptive_integration,
            reason=reason,
        )
