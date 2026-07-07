"""Repository for deterministic experience knowledge profiles."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .knowledge_observation import ExperienceKnowledgeObservation
from .knowledge_profile import ExperienceKnowledgeProfile


class ExperienceKnowledgeRepository:
    """Group validated experience by market regime before signal context."""

    def __init__(self, observations: Iterable[Mapping[str, Any]]) -> None:
        self.observations = [ExperienceKnowledgeObservation.from_mapping(item) for item in observations]

    @property
    def invalid_market_regime_count(self) -> int:
        return sum(1 for item in self.observations if not item.has_market_regime)

    def build_profiles(self) -> tuple[ExperienceKnowledgeProfile, ...]:
        grouped: dict[tuple[str, str], list[ExperienceKnowledgeObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.has_market_regime:
                grouped[(observation.market_regime, observation.signal_context)].append(observation)

        profiles = [self._build_profile(key, values) for key, values in grouped.items()]
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))

    def _build_profile(
        self,
        key: tuple[str, str],
        values: list[ExperienceKnowledgeObservation],
    ) -> ExperienceKnowledgeProfile:
        market_regime, signal_context = key
        total_weight = sum(item.sample_weight for item in values)
        denominator = total_weight or 1.0
        weighted_result = sum(item.weighted_result for item in values)
        positive_weight = sum(item.positive_weight for item in values)
        adaptive_confidence = sum(item.adaptive_confidence * item.sample_weight for item in values)
        self_evaluation_score = sum(item.self_evaluation_score * item.sample_weight for item in values)
        data_quality = sum(item.data_quality * item.sample_weight for item in values)
        knowledge_quality = sum(item.knowledge_quality * item.sample_weight for item in values)
        recency_score = sum(item.recency_score * item.sample_weight for item in values)
        reliability_score = sum(item.weighted_reliability for item in values)
        return ExperienceKnowledgeProfile(
            market_regime=market_regime,
            signal_context=signal_context,
            sample_count=len(values),
            total_weight=round(total_weight, 6),
            weighted_result=round(weighted_result, 6),
            positive_rate=round(positive_weight / denominator, 6),
            average_adaptive_confidence=round(adaptive_confidence / denominator, 6),
            average_self_evaluation_score=round(self_evaluation_score / denominator, 6),
            average_data_quality=round(data_quality / denominator, 6),
            average_knowledge_quality=round(knowledge_quality / denominator, 6),
            average_recency_score=round(recency_score / denominator, 6),
            average_reliability_score=round(reliability_score / denominator, 6),
        )
