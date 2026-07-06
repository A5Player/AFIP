"""Production Milestone E Pack 9 adaptive learning repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .learning_observation import AdaptiveLearningObservation
from .learning_profile import AdaptiveLearningProfile


class AdaptiveLearningRepository:
    """Group learning observations by market regime before learning context analysis."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | AdaptiveLearningObservation]) -> None:
        self.observations: Tuple[AdaptiveLearningObservation, ...] = tuple(
            value if isinstance(value, AdaptiveLearningObservation) else AdaptiveLearningObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[AdaptiveLearningProfile, ...]:
        grouped: dict[str, list[AdaptiveLearningObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.learning_key].append(observation)
        return tuple(AdaptiveLearningProfile.from_observations(tuple(grouped[key])) for key in sorted(grouped))

    def ready_profiles(self) -> Tuple[AdaptiveLearningProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
