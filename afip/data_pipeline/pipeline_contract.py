"""Data pipeline contract for deterministic runtime integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .data_record import FinancialDataRecord

REQUIRED_SOURCE_ORDER = ("MARKET_DATA", "REGIME_STATE", "DECISION_STATE", "EXECUTION_STATE")


@dataclass(frozen=True)
class DataPipelineContract:
    """Aggregate normalized financial data in a market-regime-first order."""

    records: tuple[FinancialDataRecord, ...]

    def __post_init__(self) -> None:
        
        order_index = {source: index for index, source in enumerate(REQUIRED_SOURCE_ORDER, start=1)}
        ordered = tuple(sorted(self.records, key=lambda item: (order_index.get(item.source_key, 99), item.sequence_index, item.timeframe)))
        object.__setattr__(self, "records", ordered)

    @property
    def usable_records(self) -> tuple[FinancialDataRecord, ...]:
        return tuple(record for record in self.records if record.is_usable)

    @property
    def source_keys(self) -> tuple[str, ...]:
        keys: list[str] = []
        for record in self.records:
            if record.source_key not in keys:
                keys.append(record.source_key)
        return tuple(keys)

    @property
    def missing_sources(self) -> tuple[str, ...]:
        present = set(self.source_keys)
        return tuple(source for source in REQUIRED_SOURCE_ORDER if source not in present)

    @property
    def sequence_is_valid(self) -> bool:
        observed = [source for source in self.source_keys if source in REQUIRED_SOURCE_ORDER]
        expected = [source for source in REQUIRED_SOURCE_ORDER if source in observed]
        return observed == expected

    @property
    def active_market_regime(self) -> str:
        for record in self.records:
            if record.source_key == "REGIME_STATE" and record.market_regime != "UNKNOWN":
                return record.market_regime
        for record in self.records:
            if record.market_regime != "UNKNOWN":
                return record.market_regime
        return "UNKNOWN"

    @property
    def average_completeness(self) -> float:
        if not self.records:
            return 0.0
        return round(sum(record.completeness_ratio for record in self.records) / len(self.records), 6)

    @property
    def average_liquidity(self) -> float:
        if not self.records:
            return 0.0
        return round(sum(record.liquidity_score for record in self.records) / len(self.records), 6)

    @property
    def maximum_spread(self) -> float:
        if not self.records:
            return 0.0
        return round(max(record.spread_points for record in self.records), 6)

    @property
    def readiness_score(self) -> float:
        if not self.records:
            return 0.0
        completeness_component = self.average_completeness * 55.0
        liquidity_component = min(45.0, self.average_liquidity * 0.45)
        return round(max(0.0, min(100.0, completeness_component + liquidity_component)), 4)

    @property
    def is_integrated(self) -> bool:
        return not self.missing_sources and self.sequence_is_valid and len(self.usable_records) == len(self.records) and self.readiness_score >= 70.0

    @classmethod
    def from_records(cls, records: Iterable[Mapping[str, Any] | FinancialDataRecord]) -> "DataPipelineContract":
        normalized: list[FinancialDataRecord] = []
        for index, record in enumerate(records, start=1):
            if isinstance(record, FinancialDataRecord):
                normalized.append(record)
            else:
                normalized.append(FinancialDataRecord.from_mapping(record, sequence_index=index))
        return cls(tuple(normalized))

    def as_dict(self) -> dict[str, object]:
        return {
            "records": [record.as_dict() for record in self.records],
            "source_keys": list(self.source_keys),
            "missing_sources": list(self.missing_sources),
            "sequence_is_valid": self.sequence_is_valid,
            "active_market_regime": self.active_market_regime,
            "average_completeness": self.average_completeness,
            "average_liquidity": self.average_liquidity,
            "maximum_spread": self.maximum_spread,
            "readiness_score": self.readiness_score,
            "is_integrated": self.is_integrated,
        }
