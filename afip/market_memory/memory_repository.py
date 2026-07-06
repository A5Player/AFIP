"""Production Milestone E Pack 3 market memory repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .memory_observation import MarketMemoryObservation
from .memory_profile import MarketMemoryProfile


class MarketMemoryRepository:
    """Group observations by market regime before memory pattern logic."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | MarketMemoryObservation]) -> None:
        self.observations: Tuple[MarketMemoryObservation, ...] = tuple(
            value if isinstance(value, MarketMemoryObservation) else MarketMemoryObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[MarketMemoryProfile, ...]:
        grouped: dict[str, list[MarketMemoryObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.regime_memory_key].append(observation)
        return tuple(
            MarketMemoryProfile.from_observations(tuple(grouped[key]))
            for key in sorted(grouped)
        )

    def ready_profiles(self) -> Tuple[MarketMemoryProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
