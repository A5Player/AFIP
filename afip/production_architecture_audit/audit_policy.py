"""Production architecture audit policy for Production Freeze Pack P1."""

from __future__ import annotations

from .audit_observation import ProductionArchitectureAuditObservation


class ProductionArchitectureAuditPolicy:
    """Deterministic policy for architecture review readiness."""

    minimum_score = 0.78

    def evaluate_reason(self, observation: ProductionArchitectureAuditObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_architecture_audit"
        if observation.circular_dependency_findings > 0:
            return "circular_dependency_review_required"
        if observation.unresolved_findings > 0:
            return "unresolved_architecture_review_required"
        if observation.audit_score < self.minimum_score:
            return "architecture_quality_review_required"
        return "production_architecture_audit_ready"

    def status_for(self, observation: ProductionArchitectureAuditObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_architecture_audit"}:
            return "BLOCKED"
        if reason == "production_architecture_audit_ready":
            return "READY"
        return "REVIEW"
