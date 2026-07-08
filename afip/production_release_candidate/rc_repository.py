"""In-memory production release candidate repository."""

from __future__ import annotations

from dataclasses import dataclass, field

from .rc_profile import ProductionReleaseCandidateProfile


@dataclass
class ProductionReleaseCandidateRepository:
    """Stores deterministic RC profiles in input order."""

    profiles: list[ProductionReleaseCandidateProfile] = field(default_factory=list)

    def append(self, profile: ProductionReleaseCandidateProfile) -> None:
        self.profiles.append(profile)

    def all(self) -> list[ProductionReleaseCandidateProfile]:
        return list(self.profiles)
