"""AI integration repository."""

from __future__ import annotations

from statistics import mean

from .integration_observation import AIIntegrationObservation
from .integration_profile import AIIntegrationProfile


class AIIntegrationRepository:
    """Build deterministic regime-first AI integration profiles."""

    def build_profiles(self, observations: tuple[AIIntegrationObservation, ...]) -> tuple[AIIntegrationProfile, ...]:
        grouped: dict[tuple[str, str], list[AIIntegrationObservation]] = {}
        for observation in observations:
            grouped.setdefault((observation.market_regime, observation.signal_context), []).append(observation)

        profiles = []
        for (market_regime, signal_context), records in grouped.items():
            profiles.append(
                AIIntegrationProfile(
                    market_regime=market_regime,
                    signal_context=signal_context,
                    planned_runtime_weight=round(mean(item.planned_runtime_weight for item in records), 6),
                    adaptation_quality=round(mean(item.adaptation_quality for item in records), 6),
                    runtime_stability=round(mean(item.runtime_stability for item in records), 6),
                    model_confidence=round(mean(item.model_confidence for item in records), 6),
                    data_quality=round(mean(item.data_quality for item in records), 6),
                    knowledge_quality=round(mean(item.knowledge_quality for item in records), 6),
                    explainability_score=round(mean(item.explainability_score for item in records), 6),
                    integration_risk=round(mean(item.integration_risk for item in records), 6),
                )
            )
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))
