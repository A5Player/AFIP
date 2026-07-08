"""Version 1 production freeze policy for Production Freeze Pack P6."""

from __future__ import annotations

from .freeze_observation import Version1FreezeObservation


class Version1FreezePolicy:
    """Applies deterministic final release readiness gates."""

    minimum_release_score = 0.85
    minimum_walk_forward_standard_score = 0.80
    minimum_deterministic_runtime_score = 0.95

    def evaluate_reason(self, observation: Version1FreezeObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.simulation_only:
            return "live_execution_not_allowed_for_version1_freeze"
        if observation.unresolved_release_items > 0:
            return "unresolved_release_items_review_required"
        if not observation.all_release_statuses_ready:
            return "release_component_review_required"
        if observation.deterministic_runtime_score < self.minimum_deterministic_runtime_score:
            return "deterministic_runtime_review_required"
        if observation.walk_forward_standard_score < self.minimum_walk_forward_standard_score:
            return "walk_forward_standard_review_required"
        if observation.release_score < self.minimum_release_score:
            return "version1_release_score_review_required"
        return "version1_production_freeze_ready"

    def status_for(self, observation: Version1FreezeObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason in {"market_regime_required", "live_execution_not_allowed_for_version1_freeze"}:
            return "BLOCKED"
        if reason == "version1_production_freeze_ready":
            return "READY"
        return "REVIEW"
