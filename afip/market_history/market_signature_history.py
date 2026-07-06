"""Historical repository for market signature occurrence tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from afip.market_history.historical_market_observation import HistoricalMarketObservation


@dataclass
class MarketSignatureHistoryRecord:
    """Historical statistics for a market signature."""

    signature_id: str
    occurrence_count: int = 0
    direction_counts: dict[str, int] = field(default_factory=dict)
    regime_counts: dict[str, int] = field(default_factory=dict)
    macro_bias_counts: dict[str, int] = field(default_factory=dict)
    institutional_bias_counts: dict[str, int] = field(default_factory=dict)
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    def observe(self, observation: HistoricalMarketObservation) -> None:
        self.occurrence_count += 1
        self.first_seen = self.first_seen or observation.observed_at
        self.last_seen = observation.observed_at
        self._count(self.direction_counts, observation.direction)
        self._count(self.regime_counts, observation.market_regime)
        self._count(self.macro_bias_counts, observation.macro_bias)
        self._count(self.institutional_bias_counts, observation.institutional_bias)

    @staticmethod
    def _count(values: dict[str, int], key: str) -> None:
        values[key] = values.get(key, 0) + 1

    @staticmethod
    def _dominant(values: dict[str, int]) -> str:
        if not values:
            return "NEUTRAL"
        return sorted(values.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def as_dict(self) -> dict[str, object]:
        return {
            "signature_id": self.signature_id,
            "occurrence_count": self.occurrence_count,
            "dominant_direction": self._dominant(self.direction_counts),
            "dominant_regime": self._dominant(self.regime_counts),
            "dominant_macro_bias": self._dominant(self.macro_bias_counts),
            "dominant_institutional_bias": self._dominant(self.institutional_bias_counts),
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class MarketSignatureHistoryRepository:
    """Track market signature history without duplicating repeated observations."""

    def __init__(self) -> None:
        self._records: dict[str, MarketSignatureHistoryRecord] = {}

    def observe(self, observation: HistoricalMarketObservation) -> MarketSignatureHistoryRecord:
        record = self._records.get(observation.signature_id)
        if record is None:
            record = MarketSignatureHistoryRecord(signature_id=observation.signature_id)
            self._records[observation.signature_id] = record
        record.observe(observation)
        return record

    def get(self, signature_id: str) -> MarketSignatureHistoryRecord | None:
        return self._records.get(signature_id)

    def records(self) -> list[MarketSignatureHistoryRecord]:
        return sorted(self._records.values(), key=lambda item: (-item.occurrence_count, item.signature_id))

    def summary(self) -> dict[str, object]:
        return {
            "status": "MARKET_SIGNATURE_HISTORY_READY",
            "unique_signatures": len(self._records),
            "total_occurrences": sum(record.occurrence_count for record in self._records.values()),
            "top_signatures": [record.as_dict() for record in self.records()[:5]],
        }
