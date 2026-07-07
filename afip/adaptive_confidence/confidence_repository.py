"""Repository for deterministic adaptive confidence profiles."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .confidence_observation import AdaptiveConfidenceObservation
from .confidence_profile import AdaptiveConfidenceProfile


class AdaptiveConfidenceRepository:
    """Group confidence evidence by market regime before signal context."""

    def __init__(self, observations: Iterable[Mapping[str, Any]]) -> None:
        self.observations = [AdaptiveConfidenceObservation.from_mapping(item) for item in observations]

    @property
    def invalid_market_regime_count(self) -> int:
        return sum(1 for item in self.observations if not item.has_market_regime)

    def build_profiles(self) -> tuple[AdaptiveConfidenceProfile, ...]:
        grouped: dict[tuple[str, str], list[AdaptiveConfidenceObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.has_market_regime:
                grouped[(observation.market_regime, observation.signal_context)].append(observation)

        profiles = [self._build_profile(key, values) for key, values in grouped.items()]
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.signal_context)))

    def _build_profile(
        self,
        key: tuple[str, str],
        values: list[AdaptiveConfidenceObservation],
    ) -> AdaptiveConfidenceProfile:
        market_regime, signal_context = key
        total_samples = sum(item.sample_size for item in values)
        denominator = total_samples or 1.0
        raw_confidence = sum(item.weighted_raw_confidence for item in values)
        evidence_quality = sum(item.weighted_evidence_quality for item in values)
        self_evaluation_score = sum(item.self_evaluation_score * item.sample_size for item in values)
        data_quality = sum(item.data_quality * item.sample_size for item in values)
        knowledge_quality = sum(item.knowledge_quality * item.sample_size for item in values)
        stability_score = sum(item.stability_score * item.sample_size for item in values)
        return AdaptiveConfidenceProfile(
            market_regime=market_regime,
            signal_context=signal_context,
            sample_count=len(values),
            total_samples=round(total_samples, 6),
            average_raw_confidence=round(raw_confidence / denominator, 6),
            average_evidence_quality=round(evidence_quality / denominator, 6),
            average_self_evaluation_score=round(self_evaluation_score / denominator, 6),
            average_data_quality=round(data_quality / denominator, 6),
            average_knowledge_quality=round(knowledge_quality / denominator, 6),
            average_stability_score=round(stability_score / denominator, 6),
        )
