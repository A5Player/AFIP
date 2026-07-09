"""Market session and trading calendar models for Production Bring-up Pack 4.

The calendar layer is read-only operational intelligence. It explains market
open, market close, weekend, holiday, active session, and trading permission
for the dashboard without enabling live execution or changing trading logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MarketCalendarReport:
    """Deterministic market calendar and session report for XM GOLD#."""

    status: str
    reason: str
    broker: str
    symbol: str
    market_open: bool
    market_closed: bool
    weekend: bool
    holiday: bool
    holiday_name: str
    active_sessions: tuple[str, ...]
    primary_session: str
    london_session: bool
    new_york_session: bool
    asia_session: bool
    trading_allowed: bool
    trading_block_reason: str
    dashboard_market_status: str
    current_time_utc: str
    next_review_time_utc: str
    calendar_gate: str
    dashboard_message_th: str
    dashboard_message_en: str
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP Market Session Calendar\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Market Open: {self.market_open}\n"
            f"Weekend: {self.weekend}\n"
            f"Holiday: {self.holiday_name}\n"
            f"Session: {self.primary_session}\n"
            f"Trading Allowed: {self.trading_allowed}\n"
            f"Block Reason: {self.trading_block_reason}"
        )
