"""Selective market snapshot repository for important lifecycle points."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


IMPORTANT_STAGES = {"PRE_ENTRY", "POST_ENTRY", "PRE_EXIT", "POST_EXIT", "EVENT_REVIEW", "DAILY_REVIEW"}


@dataclass(frozen=True)
class MarketSnapshotRecord:
    """Compact snapshot retained only at useful financial review stages."""

    snapshot_id: str
    stage: str
    signature_id: str
    observed_at: datetime
    data: Mapping[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "stage": self.stage,
            "signature_id": self.signature_id,
            "observed_at": self.observed_at.isoformat(),
            "data": dict(self.data),
        }


class MarketSnapshotRepository:
    """Keep selected snapshots instead of storing every tick or candle update."""

    def __init__(self, *, max_snapshots: int = 500) -> None:
        self.max_snapshots = max(1, int(max_snapshots))
        self._snapshots: list[MarketSnapshotRecord] = []

    def should_store(self, stage: str, *, changed: bool = False, important: bool = False) -> bool:
        stage_value = str(stage).upper()
        return stage_value in IMPORTANT_STAGES or bool(changed) or bool(important)

    def store(
        self,
        *,
        stage: str,
        signature_id: str,
        data: Mapping[str, object],
        observed_at: datetime | None = None,
        changed: bool = False,
        important: bool = False,
    ) -> MarketSnapshotRecord | None:
        if not self.should_store(stage, changed=changed, important=important):
            return None
        timestamp = observed_at or datetime.now(timezone.utc)
        snapshot_id = f"{timestamp.strftime('%Y%m%d%H%M%S')}_{signature_id}_{str(stage).upper()}"
        record = MarketSnapshotRecord(snapshot_id=snapshot_id, stage=str(stage).upper(), signature_id=str(signature_id), observed_at=timestamp, data=dict(data))
        self._snapshots.append(record)
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots = self._snapshots[-self.max_snapshots :]
        return record

    def list_recent(self, limit: int = 10) -> list[MarketSnapshotRecord]:
        return self._snapshots[-max(0, int(limit)) :]

    def summary(self) -> dict[str, object]:
        return {
            "status": "MARKET_SNAPSHOT_REPOSITORY_READY",
            "stored_snapshots": len(self._snapshots),
            "max_snapshots": self.max_snapshots,
            "storage_policy": "selective_lifecycle_snapshots",
        }
