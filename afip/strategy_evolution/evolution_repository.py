"""Strategy evolution repository."""

from __future__ import annotations

from collections import defaultdict

from .evolution_observation import StrategyEvolutionObservation
from .evolution_profile import StrategyEvolutionProfile


class StrategyEvolutionRepository:
    """Build deterministic strategy evolution profiles from knowledge evidence."""

    def build_profiles(self, observations: tuple[StrategyEvolutionObservation, ...]) -> tuple[StrategyEvolutionProfile, ...]:
        grouped: dict[tuple[str, str], list[StrategyEvolutionObservation]] = defaultdict(list)
        for item in observations:
            grouped[(item.market_regime, item.signal_context)].append(item)

        profiles: list[StrategyEvolutionProfile] = []
        for (market_regime, signal_context), items in grouped.items():
            total_weight = sum(item.sample_count for item in items)
            if total_weight == 0.0:
                continue
            profiles.append(
                StrategyEvolutionProfile(
                    market_regime=market_regime,
                    signal_context=signal_context,
                    sample_count=len(items),
                    total_weight=total_weight,
                    average_experience_score=round(sum(item.weighted_experience_score for item in items) / total_weight, 6),
                    average_expectancy=round(sum(item.weighted_expectancy for item in items) / total_weight, 6),
                    average_positive_rate=round(sum(item.weighted_positive_rate for item in items) / total_weight, 6),
                    average_evidence_quality=round(sum(item.weighted_evidence_quality for item in items) / total_weight, 6),
                    average_data_quality=round(sum(item.data_quality * item.sample_count for item in items) / total_weight, 6),
                    average_knowledge_quality=round(sum(item.knowledge_quality * item.sample_count for item in items) / total_weight, 6),
                    average_reliability_score=round(sum(item.reliability_score * item.sample_count for item in items) / total_weight, 6),
                    average_current_strategy_weight=round(
                        sum(item.current_strategy_weight * item.sample_count for item in items) / total_weight,
                        6,
                    ),
                )
            )
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))
