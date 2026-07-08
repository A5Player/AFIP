"""In-memory walk-forward simulation profile repository."""

from __future__ import annotations

from .walk_profile import WalkForwardProfile


class WalkForwardRepository:
    """Stores generated walk-forward profiles for deterministic inspection."""

    def __init__(self) -> None:
        self._profiles: list[WalkForwardProfile] = []

    def append(self, profile: WalkForwardProfile) -> None:
        self._profiles.append(profile)

    def all(self) -> list[WalkForwardProfile]:
        return list(self._profiles)

    def ready_count(self) -> int:
        return sum(1 for profile in self._profiles if profile.status == "READY")
