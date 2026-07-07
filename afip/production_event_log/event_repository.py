"""In-memory production event repository for deterministic tests and runtime review."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .event_profile import ProductionEventProfile


@dataclass
class ProductionEventRepository:
    """Simple append-only repository contract for production event profiles."""

    _profiles: List[ProductionEventProfile] = field(default_factory=list)

    def append(self, profile: ProductionEventProfile) -> None:
        self._profiles.append(profile)

    def extend(self, profiles: Iterable[ProductionEventProfile]) -> None:
        for profile in profiles:
            self.append(profile)

    def all(self) -> list[ProductionEventProfile]:
        return list(self._profiles)

    def latest(self) -> ProductionEventProfile | None:
        if not self._profiles:
            return None
        return self._profiles[-1]
