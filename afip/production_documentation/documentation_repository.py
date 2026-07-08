"""In-memory production documentation repository for deterministic tests."""

from __future__ import annotations

from .documentation_profile import ProductionDocumentationProfile


class ProductionDocumentationRepository:
    """Stores documentation profiles without external side effects."""

    def __init__(self) -> None:
        self._items: list[ProductionDocumentationProfile] = []

    def append(self, profile: ProductionDocumentationProfile) -> None:
        self._items.append(profile)

    def all(self) -> list[ProductionDocumentationProfile]:
        return list(self._items)
