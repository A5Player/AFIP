"""Compact historical market database using aggregation-first storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from afip.market_history.historical_market_observation import HistoricalMarketObservation


@dataclass
class CompactHistoricalRecord:
    """Aggregated record for repeated historical market observations."""

    compact_key: str
    sample_observation: HistoricalMarketObservation
    occurrence_count: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    confidence_total: float = 0.0
    spread_total: float = 0.0
    volatility_total: float = 0.0

    def observe(self, observation: HistoricalMarketObservation) -> None:
        self.occurrence_count += 1
        self.first_seen = self.first_seen or observation.observed_at
        self.last_seen = observation.observed_at
        self.confidence_total += float(observation.confidence)
        self.spread_total += float(observation.spread_points)
        self.volatility_total += float(observation.volatility_points)

    @property
    def average_confidence(self) -> float:
        return self.confidence_total / self.occurrence_count if self.occurrence_count else 0.0

    @property
    def average_spread(self) -> float:
        return self.spread_total / self.occurrence_count if self.occurrence_count else 0.0

    @property
    def average_volatility(self) -> float:
        return self.volatility_total / self.occurrence_count if self.occurrence_count else 0.0

    def as_dict(self) -> dict[str, object]:
        return {
            "compact_key": self.compact_key,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "average_confidence": round(self.average_confidence, 4),
            "average_spread": round(self.average_spread, 4),
            "average_volatility": round(self.average_volatility, 4),
            "sample_observation": self.sample_observation.as_dict(),
        }


class HistoricalMarketDatabase:
    """In-memory foundation that stores repeated observations as compact records."""

    def __init__(self) -> None:
        self._records: dict[str, CompactHistoricalRecord] = {}
        self._important_observations: list[HistoricalMarketObservation] = []

    def observe(self, observation: HistoricalMarketObservation) -> CompactHistoricalRecord:
        key = observation.compact_key()
        record = self._records.get(key)
        if record is None:
            record = CompactHistoricalRecord(compact_key=key, sample_observation=observation)
            self._records[key] = record
        record.observe(observation)
        if observation.stage in {"ENTRY", "EXIT", "NEWS", "SESSION_CLOSE", "REVIEW"}:
            self._important_observations.append(observation)
        return record

    def get(self, compact_key: str) -> CompactHistoricalRecord | None:
        return self._records.get(compact_key)

    def records(self) -> list[CompactHistoricalRecord]:
        return sorted(self._records.values(), key=lambda item: (-item.occurrence_count, item.compact_key))

    def important_observations(self, limit: int = 20) -> list[HistoricalMarketObservation]:
        return list(self._important_observations[-limit:])

    def summary(self) -> dict[str, object]:
        total = sum(record.occurrence_count for record in self._records.values())
        unique = len(self._records)
        return {
            "status": "HISTORICAL_MARKET_DATABASE_READY",
            "unique_records": unique,
            "total_observations": total,
            "important_observations": len(self._important_observations),
            "compression_ratio": round(total / unique, 2) if unique else 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
