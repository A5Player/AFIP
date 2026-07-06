"""Production Milestone E Pack 7 portfolio intelligence repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .portfolio_observation import PortfolioObservation
from .portfolio_profile import PortfolioProfile


class PortfolioRepository:
    """Group portfolio observations by market regime before portfolio scope analysis."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | PortfolioObservation]) -> None:
        self.observations: Tuple[PortfolioObservation, ...] = tuple(
            value if isinstance(value, PortfolioObservation) else PortfolioObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[PortfolioProfile, ...]:
        grouped: dict[str, list[PortfolioObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.portfolio_key].append(observation)
        return tuple(PortfolioProfile.from_observations(tuple(grouped[key])) for key in sorted(grouped))

    def ready_profiles(self) -> Tuple[PortfolioProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
