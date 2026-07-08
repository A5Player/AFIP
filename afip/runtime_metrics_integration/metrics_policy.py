"""Runtime metrics integration policy for deterministic production review."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics_observation import RuntimeMetricsObservation


@dataclass(frozen=True)
class RuntimeMetricsPolicy:
    """Deterministic policy that reviews runtime metrics before production hardening."""

    minimum_evidence_quality: float = 0.72
    minimum_event_log_score: float = 0.70
    minimum_observability_score: float = 0.70
    minimum_measurement_quality: float = 0.70
    minimum_latency_efficiency: float = 0.35
    minimum_resource_efficiency: float = 0.35
    maximum_memory_usage_ratio: float = 0.85

    def evaluate_reason(self, observation: RuntimeMetricsObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.has_configuration_version:
            return "configuration_version_required"
        if not observation.feature_flag_enabled:
            return "runtime_metrics_feature_flag_not_enabled"
        if observation.event_log_score < self.minimum_event_log_score:
            return "production_event_log_review_required"
        if observation.observability_score < self.minimum_observability_score:
            return "runtime_observability_review_required"
        if observation.measurement_quality < self.minimum_measurement_quality:
            return "runtime_metrics_measurement_review_required"
        if observation.memory_usage_ratio > self.maximum_memory_usage_ratio:
            return "runtime_memory_review_required"
        if observation.latency_efficiency < self.minimum_latency_efficiency:
            return "runtime_latency_review_required"
        if observation.resource_efficiency < self.minimum_resource_efficiency:
            return "runtime_resource_review_required"
        if observation.evidence_quality < self.minimum_evidence_quality:
            return "runtime_metrics_evidence_review_required"
        return "runtime_metrics_ready"

    def status_for(self, observation: RuntimeMetricsObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason == "market_regime_required":
            return "BLOCKED"
        if reason == "runtime_metrics_ready":
            return "READY"
        return "REVIEW"
