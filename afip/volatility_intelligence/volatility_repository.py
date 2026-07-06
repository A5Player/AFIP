"""Production Milestone E Pack 2 volatility repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .volatility_observation import VolatilityObservation
from .volatility_profile import VolatilityProfile


class VolatilityRepository:
    """Group observations by market regime before volatility or direction logic."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | VolatilityObservation]) -> None:
        self.observations: Tuple[VolatilityObservation, ...] = tuple(
            value if isinstance(value, VolatilityObservation) else VolatilityObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[VolatilityProfile, ...]:
        grouped: dict[str, list[VolatilityObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.regime_volatility_key].append(observation)
        return tuple(
            VolatilityProfile.from_observations(tuple(grouped[key]))
            for key in sorted(grouped)
        )

    def ready_profiles(self) -> Tuple[VolatilityProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
