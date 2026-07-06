"""Replay timeline preparation for historical market snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.replay.replay_snapshot import ReplaySnapshot


@dataclass
class ReplayTimeline:
    """Ordered timeline of replay snapshots with compact summary metrics."""

    snapshots: list[ReplaySnapshot] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.snapshots = sorted(self.snapshots, key=lambda item: item.observed_at)

    def __len__(self) -> int:
        return len(self.snapshots)

    def is_empty(self) -> bool:
        return len(self.snapshots) == 0

    def first(self) -> ReplaySnapshot | None:
        return self.snapshots[0] if self.snapshots else None

    def last(self) -> ReplaySnapshot | None:
        return self.snapshots[-1] if self.snapshots else None

    def direction_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for snapshot in self.snapshots:
            counts[snapshot.direction] = counts.get(snapshot.direction, 0) + 1
        return counts

    def regime_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for snapshot in self.snapshots:
            counts[snapshot.market_regime] = counts.get(snapshot.market_regime, 0) + 1
        return counts

    def average_spread(self) -> float:
        if not self.snapshots:
            return 0.0
        return round(sum(item.spread_points for item in self.snapshots) / len(self.snapshots), 4)

    def average_volatility(self) -> float:
        if not self.snapshots:
            return 0.0
        return round(sum(item.volatility_points for item in self.snapshots) / len(self.snapshots), 4)

    def as_dict(self) -> dict[str, object]:
        first = self.first()
        last = self.last()
        return {
            "snapshot_count": len(self.snapshots),
            "start_at": first.observed_at.isoformat() if first else None,
            "end_at": last.observed_at.isoformat() if last else None,
            "direction_counts": self.direction_counts(),
            "market_regime_counts": self.regime_counts(),
            "average_spread_points": self.average_spread(),
            "average_volatility_points": self.average_volatility(),
        }
