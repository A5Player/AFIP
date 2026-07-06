"""Market holiday and low-liquidity session detection for macro runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class MarketHolidayState:
    """Holiday detection result for production review."""

    status: str
    date_label: str
    is_holiday: bool
    liquidity_state: str
    trade_instruction: str
    reason: str


class MarketHolidayCalendar:
    """Detect known low-liquidity dates without requiring a paid service."""

    def __init__(self, holiday_dates: Iterable[date | str] | None = None) -> None:
        self.holiday_dates = frozenset(self._normalize_date(value) for value in (holiday_dates or ()))

    def assess(self, now: datetime | date | None = None) -> MarketHolidayState:
        target_date = self._current_date(now)
        if target_date.weekday() >= 5:
            return MarketHolidayState(
                status="MARKET_HOLIDAY_READY",
                date_label=target_date.isoformat(),
                is_holiday=True,
                liquidity_state="WEEKEND_CLOSED",
                trade_instruction="NO_NEW_POSITION",
                reason="weekend_market_closed",
            )
        if target_date in self.holiday_dates:
            return MarketHolidayState(
                status="MARKET_HOLIDAY_READY",
                date_label=target_date.isoformat(),
                is_holiday=True,
                liquidity_state="HOLIDAY_THIN_LIQUIDITY",
                trade_instruction="REDUCE_NEW_EXPOSURE",
                reason="configured_market_holiday",
            )
        return MarketHolidayState(
            status="MARKET_HOLIDAY_READY",
            date_label=target_date.isoformat(),
            is_holiday=False,
            liquidity_state="NORMAL_LIQUIDITY_REVIEW",
            trade_instruction="NORMAL_REVIEW",
            reason="no_holiday_restriction",
        )

    def assess_dict(self, now: datetime | date | None = None) -> dict[str, object]:
        result = self.assess(now)
        return {
            "status": result.status,
            "date_label": result.date_label,
            "is_holiday": result.is_holiday,
            "liquidity_state": result.liquidity_state,
            "trade_instruction": result.trade_instruction,
            "reason": result.reason,
        }

    def _current_date(self, now: datetime | date | None) -> date:
        if now is None:
            return datetime.now(timezone.utc).date()
        if isinstance(now, datetime):
            value = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).date()
        return now

    def _normalize_date(self, value: date | str) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
