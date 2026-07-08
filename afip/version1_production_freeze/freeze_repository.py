"""In-memory Version 1 production freeze repository for Production Freeze Pack P6."""

from __future__ import annotations

from .freeze_profile import Version1FreezeProfile


class Version1FreezeRepository:
    """Stores final release profiles during deterministic evaluation."""

    def __init__(self) -> None:
        self._items: list[Version1FreezeProfile] = []

    def append(self, profile: Version1FreezeProfile) -> None:
        self._items.append(profile)

    def all(self) -> list[Version1FreezeProfile]:
        return list(self._items)
