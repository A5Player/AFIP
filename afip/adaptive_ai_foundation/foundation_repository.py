"""Repository for deterministic adaptive AI foundation profiles."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .foundation_observation import AdaptiveAIFoundationObservation
from .foundation_profile import AdaptiveAIFoundationProfile


class AdaptiveAIFoundationRepository:
    """Group observations by market regime before evaluating signal context."""

    def __init__(self, observations: Iterable[Mapping[str, Any]]) -> None:
        self.observations = [AdaptiveAIFoundationObservation.from_mapping(item) for item in observations]

    @property
    def invalid_regime_count(self) -> int:
        return sum(1 for item in self.observations if not item.has_regime)

    def build_profiles(self) -> tuple[AdaptiveAIFoundationProfile, ...]:
        grouped: dict[str, list[AdaptiveAIFoundationObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.has_regime:
                grouped[observation.market_regime].append(observation)

        profiles = [self._build_profile(regime, values) for regime, values in grouped.items()]
        return tuple(sorted(profiles, key=lambda item: item.market_regime))

    def _build_profile(self, regime: str, values: list[AdaptiveAIFoundationObservation]) -> AdaptiveAIFoundationProfile:
        total_weight = sum(item.sample_weight for item in values)
        weighted_result = sum(item.weighted_result for item in values)
        winning_weight = sum(item.sample_weight for item in values if item.result_amount > 0.0)
        confidence_weighted = sum(item.confidence_score * item.sample_weight for item in values)
        quality_weighted = sum(item.knowledge_quality * item.sample_weight for item in values)
        denominator = total_weight or 1.0
        expectancy = weighted_result / denominator
        return AdaptiveAIFoundationProfile(
            market_regime=regime,
            sample_count=len(values),
            total_weight=round(total_weight, 6),
            weighted_result=round(weighted_result, 6),
            win_rate=round(winning_weight / denominator, 6),
            average_confidence=round(confidence_weighted / denominator, 6),
            average_knowledge_quality=round(quality_weighted / denominator, 6),
            adaptive_bias="POSITIVE_EXPECTANCY" if expectancy > 0.0 else "NEGATIVE_EXPECTANCY" if expectancy < 0.0 else "NEUTRAL_EXPECTANCY",
        )
