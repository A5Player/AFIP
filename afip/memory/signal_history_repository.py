"""Production Milestone B Pack 9 - signal history repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class SignalHistoryRecord:
    """Normalized historical signal observation."""

    signal_name: str
    direction: str
    confidence: float
    market_regime: str
    timestamp: str = ""

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SignalHistoryRecord":
        return cls(
            signal_name=str(payload.get("signal_name", payload.get("name", "UNKNOWN"))).upper(),
            direction=str(payload.get("direction", "FLAT")).upper(),
            confidence=_bounded_score(payload.get("confidence", 0.0)),
            market_regime=str(payload.get("market_regime", payload.get("regime", "NEUTRAL"))).upper(),
            timestamp=str(payload.get("timestamp", "")),
        )


@dataclass(frozen=True)
class SignalHistoryRepositoryResult:
    status: str
    records: tuple[SignalHistoryRecord, ...]
    buy_count: int
    sell_count: int
    average_confidence: float
    reason: str


class SignalHistoryRepository:
    """Store signal observations in a deterministic in-memory representation."""

    def build(self, signals: Iterable[SignalHistoryRecord | Mapping[str, Any]]) -> SignalHistoryRepositoryResult:
        records = tuple(item if isinstance(item, SignalHistoryRecord) else SignalHistoryRecord.from_mapping(item) for item in signals)
        if not records:
            return SignalHistoryRepositoryResult("SIGNAL_HISTORY_EMPTY", tuple(), 0, 0, 0.0, "no_signal_history")
        buy_count = sum(1 for item in records if item.direction == "BUY")
        sell_count = sum(1 for item in records if item.direction == "SELL")
        average_confidence = round(sum(item.confidence for item in records) / len(records), 4)
        status = "SIGNAL_HISTORY_READY" if average_confidence >= 50.0 else "SIGNAL_HISTORY_REVIEW"
        reason = "signal_history_available" if status == "SIGNAL_HISTORY_READY" else "signal_history_confidence_review"
        return SignalHistoryRepositoryResult(status, records, buy_count, sell_count, average_confidence, reason)


def _bounded_score(value: Any) -> float:
    numeric = float(value)
    if numeric <= 1.0:
        numeric *= 100.0
    return round(min(100.0, max(0.0, numeric)), 4)
