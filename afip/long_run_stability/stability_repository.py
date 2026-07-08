"""In-memory long-run stability repository for deterministic runtime review."""

from __future__ import annotations

from dataclasses import dataclass, field

from .stability_profile import LongRunStabilityProfile


@dataclass
class LongRunStabilityRepository:
    """Append-only in-memory store for long-run stability profiles."""

    profiles: list[LongRunStabilityProfile] = field(default_factory=list)

    def append(self, profile: LongRunStabilityProfile) -> None:
        self.profiles.append(profile)

    def all(self) -> list[LongRunStabilityProfile]:
        return list(self.profiles)
