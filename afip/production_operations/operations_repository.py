"""In-memory production operations repository for deterministic tests."""

from __future__ import annotations

from .operations_profile import ProductionOperationsProfile


class ProductionOperationsRepository:
    """Stores operations profiles without external side effects."""

    def __init__(self) -> None:
        self._items: list[ProductionOperationsProfile] = []

    def append(self, profile: ProductionOperationsProfile) -> None:
        self._items.append(profile)

    def all(self) -> list[ProductionOperationsProfile]:
        return list(self._items)
