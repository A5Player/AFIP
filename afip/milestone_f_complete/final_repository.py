"""Milestone F completion profile repository."""

from __future__ import annotations

from .final_observation import MilestoneFCompletionObservation
from .final_profile import MilestoneFCompletionProfile


class MilestoneFCompletionRepository:
    """Build regime-first Milestone F completion profiles from production readiness evidence."""

    def build_profiles(
        self,
        observations: tuple[MilestoneFCompletionObservation, ...],
    ) -> tuple[MilestoneFCompletionProfile, ...]:
        profiles = tuple(
            MilestoneFCompletionProfile(
                market_regime=item.market_regime,
                signal_context=item.signal_context,
                production_readiness_score=item.production_readiness_score,
                production_runtime_weight=item.production_runtime_weight,
                readiness_evidence_quality=item.readiness_evidence_quality,
                data_quality=item.data_quality,
                knowledge_quality=item.knowledge_quality,
                strategy_quality=item.strategy_quality,
                runtime_stability=item.runtime_stability,
                validation_quality=item.validation_quality,
                monitoring_quality=item.monitoring_quality,
                rollback_readiness=item.rollback_readiness,
                documentation_quality=item.documentation_quality,
                handoff_quality=item.handoff_quality,
                completion_risk=item.completion_risk,
            )
            for item in observations
        )
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))
