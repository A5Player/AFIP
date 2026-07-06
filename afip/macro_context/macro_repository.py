"""Production Milestone E Pack 8 macro context repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .macro_observation import MacroObservation
from .macro_profile import MacroProfile


class MacroRepository:
    """Group macro observations by market regime before macro theme analysis."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | MacroObservation]) -> None:
        self.observations: Tuple[MacroObservation, ...] = tuple(
            value if isinstance(value, MacroObservation) else MacroObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[MacroProfile, ...]:
        grouped: dict[str, list[MacroObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.macro_key].append(observation)
        return tuple(MacroProfile.from_observations(tuple(grouped[key])) for key in sorted(grouped))

    def ready_profiles(self) -> Tuple[MacroProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
