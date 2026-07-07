"""Runtime adaptation repository."""

from __future__ import annotations

from .adaptation_observation import RuntimeAdaptationObservation
from .adaptation_profile import RuntimeAdaptationProfile


class RuntimeAdaptationRepository:
    """Build deterministic runtime adaptation profiles from strategy evolution evidence."""

    def build_profiles(self, observations: tuple[RuntimeAdaptationObservation, ...]) -> tuple[RuntimeAdaptationProfile, ...]:
        profiles = [
            RuntimeAdaptationProfile(
                market_regime=item.market_regime,
                signal_context=item.signal_context,
                proposed_strategy_weight=item.proposed_strategy_weight,
                current_runtime_weight=item.current_runtime_weight,
                evolution_pressure=item.evolution_pressure,
                adaptation_quality=item.adaptation_quality,
                data_quality=item.data_quality,
                knowledge_quality=item.knowledge_quality,
                stability_score=item.stability_score,
                execution_cost=item.execution_cost,
            )
            for item in observations
        ]
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))
