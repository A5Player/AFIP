"""Production hardening profile for Production Milestone G Pack 5."""

from __future__ import annotations

from dataclasses import dataclass

from .hardening_observation import ProductionHardeningObservation


@dataclass(frozen=True)
class ProductionHardeningProfile:
    """Deterministic profile summarizing production hardening readiness."""

    market_regime: str
    signal_context: str
    runtime_component: str
    feature_flag_state: str
    configuration_version: str
    observability_score: float
    event_log_score: float
    feature_flag_score: float
    runtime_metrics_score: float
    dependency_alignment: float
    rollback_readiness: float
    monitoring_coverage: float
    integration_quality: float
    hardening_score: float
    status: str
    review_required: bool
    reason: str

    @classmethod
    def from_observation(cls, observation: ProductionHardeningObservation, status: str, reason: str) -> "ProductionHardeningProfile":
        return cls(
            market_regime=observation.market_regime,
            signal_context=observation.signal_context,
            runtime_component=observation.runtime_component,
            feature_flag_state=observation.feature_flag_state,
            configuration_version=observation.configuration_version,
            observability_score=round(observation.observability_score, 4),
            event_log_score=round(observation.event_log_score, 4),
            feature_flag_score=round(observation.feature_flag_score, 4),
            runtime_metrics_score=round(observation.runtime_metrics_score, 4),
            dependency_alignment=round(observation.dependency_alignment, 4),
            rollback_readiness=round(observation.rollback_readiness, 4),
            monitoring_coverage=round(observation.monitoring_coverage, 4),
            integration_quality=round(observation.integration_quality, 4),
            hardening_score=round(observation.hardening_score, 4),
            status=status,
            review_required=status != "READY",
            reason=reason,
        )

    @property
    def readiness_gate(self) -> str:
        if self.status == "BLOCKED":
            return "BLOCKED"
        if self.status == "REVIEW":
            return "REVIEW_REQUIRED"
        return "PRODUCTION_READY"
