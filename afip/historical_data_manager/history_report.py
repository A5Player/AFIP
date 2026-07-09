"""Historical Data Manager report objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HistoricalDataManagerReport:
    status: str
    reason: str
    history_gate: str
    broker: str
    symbol: str
    requested_days: int
    downloaded_bars: int
    missing_bars: int
    duplicate_bars: int
    quality_score: float
    walk_forward_ready: bool
    research_ready: bool
    validation_items: tuple[str, ...]
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP Historical Data Manager\n"
            f"Status: {self.status}\n"
            f"Gate: {self.history_gate}\n"
            f"Reason: {self.reason}\n"
            f"Broker: {self.broker}\n"
            f"Symbol: {self.symbol}\n"
            f"Downloaded Bars: {self.downloaded_bars}\n"
            f"Missing Bars: {self.missing_bars}\n"
            f"Quality Score: {self.quality_score}\n"
            f"Walk Forward Ready: {self.walk_forward_ready}\n"
            f"Research Ready: {self.research_ready}"
        )
