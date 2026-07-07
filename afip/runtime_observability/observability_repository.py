"""In-memory runtime observability repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Tuple

from .metrics_profile import RuntimeObservabilityProfile


@dataclass
class RuntimeObservabilityRepository:
    """Small deterministic repository for runtime observability profiles."""

    profiles: list[RuntimeObservabilityProfile] = field(default_factory=list)

    def add(self, profile: RuntimeObservabilityProfile) -> None:
        self.profiles.append(profile)

    def all(self) -> Tuple[RuntimeObservabilityProfile, ...]:
        return tuple(self.profiles)

    def ready_profiles(self) -> Tuple[RuntimeObservabilityProfile, ...]:
        return tuple(profile for profile in self.profiles if profile.is_ready)

    @classmethod
    def from_profiles(cls, profiles: Iterable[RuntimeObservabilityProfile]) -> "RuntimeObservabilityRepository":
        repository = cls()
        for profile in profiles:
            repository.add(profile)
        return repository
