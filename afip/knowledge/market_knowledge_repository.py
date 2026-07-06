"""Compact market knowledge repository keyed by market signatures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping

from afip.knowledge.market_statistics_repository import RunningMarketStatistics


@dataclass
class MarketKnowledgeRecord:
    """Aggregated knowledge for one repeated market signature."""

    signature_id: str
    components: dict[str, str]
    statistics: RunningMarketStatistics = field(default_factory=RunningMarketStatistics)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_count: int = 1

    @property
    def occurrence_count(self) -> int:
        return self.statistics.observations

    def as_dict(self) -> dict[str, object]:
        return {
            "signature_id": self.signature_id,
            "components": dict(self.components),
            "occurrence_count": self.occurrence_count,
            "statistics": self.statistics.as_dict(),
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "source_count": self.source_count,
        }


class MarketKnowledgeRepository:
    """Store compact records so repeated conditions increase counts instead of duplicating rows."""

    def __init__(self) -> None:
        self._records: dict[str, MarketKnowledgeRecord] = {}

    def observe(
        self,
        *,
        signature: Mapping[str, object],
        result_amount: float = 0.0,
        holding_minutes: float = 0.0,
        mae: float = 0.0,
        mfe: float = 0.0,
        observed_at: datetime | None = None,
        source_count: int = 1,
    ) -> MarketKnowledgeRecord:
        signature_id = str(signature.get("signature_id", "UNKNOWN_SIGNATURE"))
        components_raw = signature.get("components", {})
        components = {str(key): str(value) for key, value in dict(components_raw).items()} if isinstance(components_raw, Mapping) else {}
        timestamp = observed_at or datetime.now(timezone.utc)
        record = self._records.get(signature_id)
        if record is None:
            record = MarketKnowledgeRecord(signature_id=signature_id, components=components, first_seen=timestamp, last_seen=timestamp)
            self._records[signature_id] = record
        record.last_seen = timestamp
        record.source_count = max(record.source_count, int(source_count))
        record.statistics.update(result_amount=result_amount, holding_minutes=holding_minutes, mae=mae, mfe=mfe)
        return record

    def get(self, signature_id: str) -> MarketKnowledgeRecord | None:
        return self._records.get(signature_id)

    def top_by_occurrence(self, limit: int = 10) -> list[MarketKnowledgeRecord]:
        return sorted(self._records.values(), key=lambda item: (-item.occurrence_count, item.signature_id))[:limit]

    def summary(self) -> dict[str, object]:
        total_observations = sum(record.occurrence_count for record in self._records.values())
        return {
            "status": "MARKET_KNOWLEDGE_READY",
            "unique_signatures": len(self._records),
            "total_observations": total_observations,
            "compression_ratio": round(total_observations / len(self._records), 2) if self._records else 0.0,
        }
