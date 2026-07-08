"""In-memory paper trading repository for deterministic tests and runtime review."""

from __future__ import annotations

from dataclasses import dataclass, field

from .paper_profile import PaperTradingProfile


@dataclass
class PaperTradingRepository:
    """Append-only in-memory store for paper trading profiles."""

    profiles: list[PaperTradingProfile] = field(default_factory=list)

    def append(self, profile: PaperTradingProfile) -> None:
        self.profiles.append(profile)

    def all(self) -> list[PaperTradingProfile]:
        return list(self.profiles)
