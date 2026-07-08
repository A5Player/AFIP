"""In-memory feature flag repository for deterministic review workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .flag_profile import FeatureFlagProfile


@dataclass
class FeatureFlagRepository:
    """Simple append-only repository contract for feature flag profiles."""

    _profiles: List[FeatureFlagProfile] = field(default_factory=list)

    def append(self, profile: FeatureFlagProfile) -> None:
        self._profiles.append(profile)

    def extend(self, profiles: Iterable[FeatureFlagProfile]) -> None:
        for profile in profiles:
            self.append(profile)

    def all(self) -> list[FeatureFlagProfile]:
        return list(self._profiles)

    def latest(self) -> FeatureFlagProfile | None:
        if not self._profiles:
            return None
        return self._profiles[-1]
