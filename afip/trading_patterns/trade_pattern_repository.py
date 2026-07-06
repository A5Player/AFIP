"""Repositories for compact trading pattern records."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.trading_patterns.trade_outcome_statistics import TradeOutcomeStatistics
from afip.trading_patterns.trade_pattern_record import TradePatternRecord


@dataclass
class TradePatternSummary:
    """Aggregated statistics for one normalized trading pattern."""

    key: str
    statistics: TradeOutcomeStatistics = field(default_factory=TradeOutcomeStatistics)
    latest_record: dict[str, object] = field(default_factory=dict)

    def observe(self, record: TradePatternRecord) -> "TradePatternSummary":
        self.statistics.observe(
            result_amount=record.result_amount,
            holding_minutes=record.holding_minutes,
            mae_points=record.mae_points,
            mfe_points=record.mfe_points,
            execution_cost_points=record.execution_cost_points,
        )
        self.latest_record = record.as_dict()
        return self

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "statistics": self.statistics.as_dict(),
            "latest_record": dict(self.latest_record),
        }


class TradePatternRepository:
    """Aggregate repeated trading patterns into compact statistical records."""

    def __init__(self) -> None:
        self._records: dict[str, TradePatternSummary] = {}

    def observe(self, record: TradePatternRecord) -> TradePatternSummary:
        summary = self._records.setdefault(record.pattern_key, TradePatternSummary(record.pattern_key))
        return summary.observe(record)

    def get(self, key: str) -> TradePatternSummary | None:
        return self._records.get(key)

    def ranked(self, limit: int = 10) -> list[TradePatternSummary]:
        return sorted(
            self._records.values(),
            key=lambda item: (
                item.statistics.expectancy,
                item.statistics.win_rate,
                item.statistics.observations,
            ),
            reverse=True,
        )[: max(0, int(limit))]

    def as_dict(self) -> dict[str, object]:
        ranked = [item.as_dict() for item in self.ranked(limit=len(self._records))]
        return {"unique_patterns": len(self._records), "patterns": ranked}


class TradingSetupRepository:
    """Aggregate more detailed trading setups while still avoiding duplicated raw storage."""

    def __init__(self) -> None:
        self._records: dict[str, TradePatternSummary] = {}

    def observe(self, record: TradePatternRecord) -> TradePatternSummary:
        summary = self._records.setdefault(record.setup_key, TradePatternSummary(record.setup_key))
        return summary.observe(record)

    def ranked(self, limit: int = 10) -> list[TradePatternSummary]:
        return sorted(
            self._records.values(),
            key=lambda item: (
                item.statistics.profit_factor,
                item.statistics.expectancy,
                item.statistics.observations,
            ),
            reverse=True,
        )[: max(0, int(limit))]

    def as_dict(self) -> dict[str, object]:
        ranked = [item.as_dict() for item in self.ranked(limit=len(self._records))]
        return {"unique_setups": len(self._records), "setups": ranked}
