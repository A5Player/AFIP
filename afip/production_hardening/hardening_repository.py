"""In-memory production hardening repository for deterministic tests and reports."""

from __future__ import annotations

from dataclasses import dataclass, field

from .hardening_profile import ProductionHardeningProfile


@dataclass
class ProductionHardeningRepository:
    """Append-only repository preserving evaluation order."""

    profiles: list[ProductionHardeningProfile] = field(default_factory=list)

    def append(self, profile: ProductionHardeningProfile) -> None:
        self.profiles.append(profile)

    def all(self) -> list[ProductionHardeningProfile]:
        return list(self.profiles)
