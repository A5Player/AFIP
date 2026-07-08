"""Production operations policy for Production Freeze Pack P4."""

from __future__ import annotations

from .operations_observation import ProductionOperationsObservation


class ProductionOperationsPolicy:
    """Applies deterministic deployment and operations readiness gates."""

    minimum_deployment_score = 0.78
    minimum_operations_score = 0.80

    def evaluate_reason(self, observation: ProductionOperationsObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_operations_review"
        if observation.unresolved_operations_items > 0:
            return "unresolved_operations_review_required"
        if observation.deployment_score < self.minimum_deployment_score:
            return "deployment_readiness_review_required"
        if observation.operations_score < self.minimum_operations_score:
            return "operations_score_review_required"
        return "production_operations_ready"

    def status_for(self, observation: ProductionOperationsObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_operations_review"}:
            return "BLOCKED"
        if reason == "production_operations_ready":
            return "READY"
        return "REVIEW"
