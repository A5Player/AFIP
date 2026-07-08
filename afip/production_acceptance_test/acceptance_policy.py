"""Production acceptance test policy for Production Freeze Pack P2."""

from __future__ import annotations

from .acceptance_observation import ProductionAcceptanceTestObservation


class ProductionAcceptanceTestPolicy:
    """Deterministic policy for production scenario acceptance readiness."""

    minimum_score = 0.80
    minimum_data_continuity = 0.72
    minimum_risk_gate = 0.74

    def evaluate_reason(self, observation: ProductionAcceptanceTestObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_acceptance_test"
        if observation.unresolved_scenarios > 0:
            return "unresolved_acceptance_scenario_review_required"
        if observation.data_continuity_score < self.minimum_data_continuity:
            return "data_continuity_review_required"
        if observation.risk_gate_score < self.minimum_risk_gate:
            return "risk_gate_review_required"
        if observation.acceptance_score < self.minimum_score:
            return "production_acceptance_review_required"
        return "production_acceptance_ready"

    def status_for(self, observation: ProductionAcceptanceTestObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_acceptance_test"}:
            return "BLOCKED"
        if reason == "production_acceptance_ready":
            return "READY"
        return "REVIEW"
