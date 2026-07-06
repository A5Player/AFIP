"""Market pattern repository for aggregated session, regime, and macro combinations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from afip.knowledge.market_statistics_repository import RunningMarketStatistics


@dataclass
class MarketPatternRecord:
    """Aggregated performance profile for one normalized market pattern."""

    pattern_key: str
    attributes: dict[str, str]
    statistics: RunningMarketStatistics = field(default_factory=RunningMarketStatistics)

    def as_dict(self) -> dict[str, object]:
        return {
            "pattern_key": self.pattern_key,
            "attributes": dict(self.attributes),
            "occurrence_count": self.statistics.observations,
            "statistics": self.statistics.as_dict(),
        }


class MarketPatternRepository:
    """Compress repeated market patterns into one statistical record."""

    def __init__(self) -> None:
        self._patterns: dict[str, MarketPatternRecord] = {}

    def key_for(self, attributes: Mapping[str, object]) -> str:
        normalized = {str(key): self._normalize(value) for key, value in sorted(attributes.items())}
        return "|".join(f"{key}:{value}" for key, value in normalized.items()) or "EMPTY_PATTERN"

    def observe(
        self,
        attributes: Mapping[str, object],
        *,
        result_amount: float = 0.0,
        holding_minutes: float = 0.0,
        mae: float = 0.0,
        mfe: float = 0.0,
    ) -> MarketPatternRecord:
        key = self.key_for(attributes)
        normalized = {str(name): self._normalize(value) for name, value in sorted(attributes.items())}
        record = self._patterns.get(key)
        if record is None:
            record = MarketPatternRecord(pattern_key=key, attributes=normalized)
            self._patterns[key] = record
        record.statistics.update(result_amount=result_amount, holding_minutes=holding_minutes, mae=mae, mfe=mfe)
        return record

    def summary(self) -> dict[str, object]:
        total = sum(item.statistics.observations for item in self._patterns.values())
        return {
            "status": "MARKET_PATTERN_REPOSITORY_READY",
            "unique_patterns": len(self._patterns),
            "total_observations": total,
            "compression_ratio": round(total / len(self._patterns), 2) if self._patterns else 0.0,
        }

    def top_by_expectancy(self, limit: int = 10) -> list[MarketPatternRecord]:
        return sorted(self._patterns.values(), key=lambda item: (-item.statistics.expectancy, item.pattern_key))[:limit]

    @staticmethod
    def _normalize(value: object) -> str:
        text = str(value).strip().upper().replace(" ", "_")
        return text or "EMPTY"
