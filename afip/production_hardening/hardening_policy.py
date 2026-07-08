"""Production hardening policy for deterministic integration readiness review."""

from __future__ import annotations

from dataclasses import dataclass

from .hardening_observation import ProductionHardeningObservation


@dataclass(frozen=True)
class ProductionHardeningPolicy:
    """Deterministic production hardening gate across Milestone G observability modules."""

    minimum_component_score: float = 0.70
    minimum_dependency_alignment: float = 0.74
    minimum_rollback_readiness: float = 0.68
    minimum_monitoring_coverage: float = 0.68
    minimum_integration_quality: float = 0.76
    minimum_hardening_score: float = 0.74

    def evaluate_reason(self, observation: ProductionHardeningObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.has_configuration_version:
            return "configuration_version_required"
        if not observation.feature_flag_enabled:
            return "feature_flag_not_enabled"
        if observation.observability_score < self.minimum_component_score:
            return "runtime_observability_review_required"
        if observation.event_log_score < self.minimum_component_score:
            return "production_event_log_review_required"
        if observation.feature_flag_score < self.minimum_component_score:
            return "feature_flag_review_required"
        if observation.runtime_metrics_score < self.minimum_component_score:
            return "runtime_metrics_review_required"
        if observation.dependency_alignment < self.minimum_dependency_alignment:
            return "dependency_alignment_review_required"
        if observation.rollback_readiness < self.minimum_rollback_readiness:
            return "rollback_readiness_review_required"
        if observation.monitoring_coverage < self.minimum_monitoring_coverage:
            return "monitoring_coverage_review_required"
        if observation.integration_quality < self.minimum_integration_quality:
            return "integration_quality_review_required"
        if observation.hardening_score < self.minimum_hardening_score:
            return "production_hardening_review_required"
        return "production_hardening_ready"

    def status_for(self, observation: ProductionHardeningObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason == "market_regime_required":
            return "BLOCKED"
        if reason == "production_hardening_ready":
            return "READY"
        return "REVIEW"
