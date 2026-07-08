"""Walk-forward historical paper simulation policy for Production Freeze Pack P5."""

from __future__ import annotations

from .walk_observation import WalkForwardObservation


class WalkForwardPolicy:
    """Applies deterministic no-lookahead simulation readiness gates."""

    minimum_historical_window_bars = 200
    minimum_simulated_orders = 10
    minimum_completion_score = 0.75
    minimum_acceptance_score = 0.72

    def evaluate_reason(self, observation: WalkForwardObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_walk_forward_simulation"
        if not observation.has_no_lookahead:
            return "lookahead_bias_detected"
        if not observation.has_enough_history or observation.historical_window_bars < self.minimum_historical_window_bars:
            return "historical_window_review_required"
        if observation.simulated_orders < self.minimum_simulated_orders:
            return "insufficient_simulated_orders"
        if observation.unresolved_simulation_items > 0:
            return "unresolved_simulation_review_required"
        if observation.completion_score < self.minimum_completion_score:
            return "order_completion_review_required"
        if observation.acceptance_score < self.minimum_acceptance_score:
            return "walk_forward_standard_review_required"
        return "walk_forward_standard_ready"

    def status_for(self, observation: WalkForwardObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {
            "market_regime_required",
            "live_execution_not_allowed_for_walk_forward_simulation",
            "lookahead_bias_detected",
        }:
            return "BLOCKED"
        if reason == "walk_forward_standard_ready":
            return "READY"
        return "REVIEW"
