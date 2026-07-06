"""Production Milestone E Pack 5 dynamic weight repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .weight_observation import DynamicWeightObservation
from .weight_profile import DynamicWeightProfile


class DynamicWeightRepository:
    """Group weight observations by market regime before intelligence contribution."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | DynamicWeightObservation]) -> None:
        self.observations: Tuple[DynamicWeightObservation, ...] = tuple(
            value if isinstance(value, DynamicWeightObservation) else DynamicWeightObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[DynamicWeightProfile, ...]:
        grouped: dict[str, list[DynamicWeightObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.regime_weight_key].append(observation)
        return tuple(
            DynamicWeightProfile.from_observations(tuple(grouped[key]))
            for key in sorted(grouped)
        )

    def ready_profiles(self) -> Tuple[DynamicWeightProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
