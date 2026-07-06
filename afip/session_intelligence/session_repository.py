"""Production Milestone E Pack 1 session repository."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Tuple

from .session_observation import SessionObservation
from .session_profile import SessionProfile


class SessionRepository:
    """Group observations by market regime before session or direction logic."""

    def __init__(self, observations: Iterable[Mapping[str, Any] | SessionObservation]) -> None:
        self.observations: Tuple[SessionObservation, ...] = tuple(
            value if isinstance(value, SessionObservation) else SessionObservation.from_mapping(value)
            for value in observations
        )

    def build_profiles(self) -> Tuple[SessionProfile, ...]:
        grouped: dict[str, list[SessionObservation]] = defaultdict(list)
        for observation in self.observations:
            if observation.is_usable:
                grouped[observation.regime_session_key].append(observation)
        profiles = tuple(
            SessionProfile.from_observations(tuple(grouped[key]))
            for key in sorted(grouped)
        )
        return profiles

    def ready_profiles(self) -> Tuple[SessionProfile, ...]:
        return tuple(profile for profile in self.build_profiles() if profile.is_ready)
