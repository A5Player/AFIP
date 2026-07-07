"""Production event log policy for deterministic runtime audit readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .event_observation import ProductionEventObservation


@dataclass(frozen=True)
class ProductionEventPolicy:
    """Deterministic event log readiness policy with configuration rollback checks."""

    minimum_evidence_quality: float = 0.74
    minimum_event_completeness: float = 0.70
    minimum_event_order_quality: float = 0.70
    minimum_config_change_quality: float = 0.70
    minimum_rollback_quality: float = 0.70
    minimum_audit_quality: float = 0.72

    def evaluate_reason(self, observation: ProductionEventObservation) -> str:
        if not observation.has_market_regime:
            return "market_regime_required"
        if not observation.has_config_version:
            return "config_version_required"
        if observation.event_completeness < self.minimum_event_completeness:
            return "event_completeness_review_required"
        if observation.event_order_quality < self.minimum_event_order_quality:
            return "event_order_review_required"
        if observation.config_change_quality < self.minimum_config_change_quality:
            return "configuration_version_review_required"
        if observation.rollback_quality < self.minimum_rollback_quality:
            return "rollback_review_required"
        if observation.audit_quality < self.minimum_audit_quality:
            return "audit_review_required"
        if observation.evidence_quality < self.minimum_evidence_quality:
            return "event_log_evidence_review_required"
        return "production_event_log_ready"

    def status_for(self, observation: ProductionEventObservation) -> str:
        reason = self.evaluate_reason(observation)
        if reason == "market_regime_required":
            return "BLOCKED"
        if reason == "production_event_log_ready":
            return "READY"
        return "REVIEW"
