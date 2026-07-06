"""Provider contract for historical market replay input."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from afip.replay.replay_snapshot import ReplaySnapshot


class HistoricalReplayProvider(Protocol):
    """Read replay snapshots for a requested period."""

    def load(self, start_at: datetime, end_at: datetime, symbol: str = "GOLD#") -> list[ReplaySnapshot]:
        """Return snapshots between start_at and end_at."""


@dataclass
class StaticHistoricalReplayProvider:
    """Deterministic replay provider used by tests and offline research."""

    snapshots: list[ReplaySnapshot] = field(default_factory=list)

    def load(self, start_at: datetime, end_at: datetime, symbol: str = "GOLD#") -> list[ReplaySnapshot]:
        requested_symbol = symbol.upper()
        return sorted(
            [
                snapshot
                for snapshot in self.snapshots
                if start_at <= snapshot.observed_at <= end_at and snapshot.symbol == requested_symbol
            ],
            key=lambda item: item.observed_at,
        )
