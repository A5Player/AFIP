"""Production readiness profile repository."""

from __future__ import annotations

from .readiness_observation import ProductionReadinessObservation
from .readiness_profile import ProductionReadinessProfile


class ProductionReadinessRepository:
    """Build regime-first production readiness profiles from validation evidence."""

    def build_profiles(
        self,
        observations: tuple[ProductionReadinessObservation, ...],
    ) -> tuple[ProductionReadinessProfile, ...]:
        profiles = tuple(
            ProductionReadinessProfile(
                market_regime=item.market_regime,
                signal_context=item.signal_context,
                validation_score=item.validation_score,
                approved_runtime_weight=item.approved_runtime_weight,
                evidence_quality=item.evidence_quality,
                data_quality=item.data_quality,
                knowledge_quality=item.knowledge_quality,
                explainability_score=item.explainability_score,
                runtime_stability=item.runtime_stability,
                validation_sample_quality=item.validation_sample_quality,
                validation_consistency=item.validation_consistency,
                validation_risk=item.validation_risk,
                deployment_control_quality=item.deployment_control_quality,
                monitoring_quality=item.monitoring_quality,
                rollback_readiness=item.rollback_readiness,
            )
            for item in observations
        )
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))
