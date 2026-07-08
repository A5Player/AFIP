"""In-memory production acceptance test repository."""

from __future__ import annotations

from .acceptance_profile import ProductionAcceptanceTestProfile


class ProductionAcceptanceTestRepository:
    """Stores deterministic acceptance profiles for runtime adapters and tests."""

    def __init__(self) -> None:
        self._profiles: list[ProductionAcceptanceTestProfile] = []

    def append(self, profile: ProductionAcceptanceTestProfile) -> None:
        self._profiles.append(profile)

    def all(self) -> list[ProductionAcceptanceTestProfile]:
        return list(self._profiles)
