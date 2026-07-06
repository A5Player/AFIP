"""Production Milestone E Pack 6 performance attribution repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .attribution_observation import PerformanceAttributionObservation
from .attribution_profile import PerformanceAttributionProfile


class PerformanceAttributionRepository:
    """Group attribution observations by market regime before source analysis."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | PerformanceAttributionObservation]) -> None:
        self.observations: Tuple[PerformanceAttributionObservation, ...] = tuple(
            value if isinstance(value, PerformanceAttributionObservation) else PerformanceAttributionObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[PerformanceAttributionProfile, ...]:
        grouped: dict[str, list[PerformanceAttributionObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.attribution_key].append(observation)
        return tuple(
            PerformanceAttributionProfile.from_observations(tuple(grouped[key]))
            for key in sorted(grouped)
        )

    def ready_profiles(self) -> Tuple[PerformanceAttributionProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
