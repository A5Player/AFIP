"""Production documentation policy for Production Freeze Pack P3."""

from __future__ import annotations

from .documentation_observation import ProductionDocumentationObservation


class ProductionDocumentationPolicy:
    """Applies deterministic documentation readiness gates."""

    minimum_coverage_score = 0.78
    minimum_documentation_score = 0.80

    def evaluate_reason(self, observation: ProductionDocumentationObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_documentation_review"
        if observation.unresolved_documentation_items > 0:
            return "unresolved_documentation_review_required"
        if observation.coverage_score < self.minimum_coverage_score:
            return "documentation_coverage_review_required"
        if observation.documentation_score < self.minimum_documentation_score:
            return "documentation_score_review_required"
        return "production_documentation_ready"

    def status_for(self, observation: ProductionDocumentationObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_documentation_review"}:
            return "BLOCKED"
        if reason == "production_documentation_ready":
            return "READY"
        return "REVIEW"
