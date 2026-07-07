"""Validation profile repository."""

from __future__ import annotations

from .validation_observation import ValidationObservation
from .validation_profile import ValidationProfile


class ValidationRepository:
    """Build regime-first validation profiles from normalized observations."""

    def build_profiles(self, observations: tuple[ValidationObservation, ...]) -> tuple[ValidationProfile, ...]:
        profiles = tuple(
            ValidationProfile(
                market_regime=item.market_regime,
                signal_context=item.signal_context,
                ai_alignment_score=item.ai_alignment_score,
                recommended_ai_weight=item.recommended_ai_weight,
                integration_quality=item.integration_quality,
                data_quality=item.data_quality,
                knowledge_quality=item.knowledge_quality,
                explainability_score=item.explainability_score,
                runtime_stability=item.runtime_stability,
                validation_sample_quality=item.validation_sample_quality,
                validation_consistency=item.validation_consistency,
                validation_risk=item.validation_risk,
            )
            for item in observations
        )
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))
