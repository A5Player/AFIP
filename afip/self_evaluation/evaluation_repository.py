"""Repository for deterministic self evaluation profiles."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .evaluation_observation import SelfEvaluationObservation
from .evaluation_profile import SelfEvaluationProfile


class SelfEvaluationRepository:
    """Group closed decisions by market regime before evaluating outcomes."""

    def __init__(self, observations: Iterable[Mapping[str, Any]]) -> None:
        self.observations = [SelfEvaluationObservation.from_mapping(item) for item in observations]

    @property
    def invalid_market_regime_count(self) -> int:
        return sum(1 for item in self.observations if not item.has_market_regime)

    def build_profiles(self) -> tuple[SelfEvaluationProfile, ...]:
        grouped: dict[tuple[str, str], list[SelfEvaluationObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.has_market_regime:
                grouped[(observation.market_regime, observation.decision_status)].append(observation)

        profiles = [self._build_profile(key, values) for key, values in grouped.items()]
        return tuple(sorted(profiles, key=lambda item: (item.market_regime, item.decision_status)))

    def _build_profile(
        self,
        key: tuple[str, str],
        values: list[SelfEvaluationObservation],
    ) -> SelfEvaluationProfile:
        market_regime, decision_status = key
        total_weight = sum(item.sample_weight for item in values)
        denominator = total_weight or 1.0
        weighted_result = sum(item.weighted_result for item in values)
        winning_weight = sum(item.sample_weight for item in values if item.realized_result > 0.0)
        expected_confidence = sum(item.expected_confidence * item.sample_weight for item in values)
        confidence_error = sum(item.confidence_error * item.sample_weight for item in values)
        data_quality = sum(item.data_quality * item.sample_weight for item in values)
        knowledge_quality = sum(item.knowledge_quality * item.sample_weight for item in values)
        return SelfEvaluationProfile(
            market_regime=market_regime,
            decision_status=decision_status,
            sample_count=len(values),
            total_weight=round(total_weight, 6),
            weighted_result=round(weighted_result, 6),
            win_rate=round(winning_weight / denominator, 6),
            average_expected_confidence=round(expected_confidence / denominator, 6),
            average_confidence_error=round(confidence_error / denominator, 6),
            average_data_quality=round(data_quality / denominator, 6),
            average_knowledge_quality=round(knowledge_quality / denominator, 6),
        )
