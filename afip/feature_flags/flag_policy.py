"""Feature flag policy for deterministic production control readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .flag_observation import FeatureFlagObservation


@dataclass(frozen=True)
class FeatureFlagPolicy:
    """Deterministic policy that reviews feature flag changes before runtime use."""

    minimum_evidence_quality: float = 0.75
    minimum_production_event_score: float = 0.70
    minimum_observability_score: float = 0.70
    minimum_rollout_quality: float = 0.72
    minimum_rollback_quality: float = 0.72
    minimum_dependency_quality: float = 0.70
    minimum_operator_review_quality: float = 0.70
    minimum_audit_quality: float = 0.72

    def evaluate_reason(self, observation: FeatureFlagObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.has_configuration_version:
            return "configuration_version_required"
        if observation.production_event_score < self.minimum_production_event_score:
            return "production_event_review_required"
        if observation.observability_score < self.minimum_observability_score:
            return "observability_review_required"
        if observation.rollout_quality < self.minimum_rollout_quality:
            return "feature_rollout_review_required"
        if observation.rollback_quality < self.minimum_rollback_quality:
            return "feature_rollback_review_required"
        if observation.dependency_quality < self.minimum_dependency_quality:
            return "feature_dependency_review_required"
        if observation.operator_review_quality < self.minimum_operator_review_quality:
            return "operator_review_required"
        if observation.audit_quality < self.minimum_audit_quality:
            return "feature_audit_review_required"
        if observation.evidence_quality < self.minimum_evidence_quality:
            return "feature_flag_evidence_review_required"
        return "feature_flag_ready"

    def status_for(self, observation: FeatureFlagObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason == "market_regime_required":
            return "BLOCKED"
        if reason == "feature_flag_ready":
            return "READY"
        return "REVIEW"
