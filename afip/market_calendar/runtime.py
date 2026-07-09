"""Market session and trading calendar monitor for Production Bring-up Pack 4."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Iterable, Mapping

from .models import MarketCalendarReport

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
_DEFAULT_HOLIDAYS = {
    "01-01": "New Year market holiday",
    "12-25": "Christmas market holiday",
}


def _text(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _text(value, default).upper()


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "ready", "open"}
    return bool(value)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    else:
        raw = _text(value, "")
        if raw:
            normalized = raw.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(normalized)
            except ValueError:
                dt = datetime.now(UTC)
        else:
            dt = datetime.now(UTC)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _holiday_map(record: Mapping[str, Any]) -> dict[str, str]:
    holidays = dict(_DEFAULT_HOLIDAYS)
    configured = record.get("holiday_calendar", record.get("holidays", ()))
    if isinstance(configured, Mapping):
        for key, value in configured.items():
            holidays[str(key)] = _text(value, "Configured market holiday")
    elif isinstance(configured, Iterable) and not isinstance(configured, (str, bytes)):
        for item in configured:
            holidays[str(item)] = "Configured market holiday"
    return holidays


def _sessions(now: datetime) -> tuple[tuple[str, bool], ...]:
    hour_value = now.hour + now.minute / 60.0
    return (
        ("Asia", 0.0 <= hour_value < 8.0),
        ("London", 7.0 <= hour_value < 16.0),
        ("New York", 12.0 <= hour_value < 21.0),
    )


class MarketCalendarRuntime:
    """Evaluate market open/close and session status for dashboard display."""

    def evaluate_one(self, record: Mapping[str, Any] | None = None) -> MarketCalendarReport:
        record = record or {}
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        live = _bool(record.get("live_execution_enabled", False)) or _upper(record.get("mode", ""), "") == "LIVE"
        if live:
            return self._blocked("live_execution_blocked_for_market_calendar")
        if broker != VERSION1_BROKER:
            return self._blocked("version1_xm_only_required_for_market_calendar", broker=broker, symbol=symbol)
        if symbol != VERSION1_SYMBOL:
            return self._blocked("version1_gold_only_required_for_market_calendar", broker=broker, symbol=symbol)

        now = _parse_datetime(record.get("current_time_utc", record.get("timestamp_utc", record.get("now_utc"))))
        weekday = now.weekday()  # Monday = 0, Sunday = 6.
        hour_value = now.hour + now.minute / 60.0
        weekend = weekday == 5 or (weekday == 6 and hour_value < 22.0) or (weekday == 4 and hour_value >= 22.0)
        holidays = _holiday_map(record)
        holiday_key = now.date().isoformat()
        month_day_key = now.strftime("%m-%d")
        holiday_name = holidays.get(holiday_key, holidays.get(month_day_key, ""))
        holiday = bool(holiday_name)

        session_flags = _sessions(now)
        active_sessions = tuple(name for name, active in session_flags if active)
        primary_session = active_sessions[-1] if active_sessions else "Closed"
        london = any(name == "London" and active for name, active in session_flags)
        new_york = any(name == "New York" and active for name, active in session_flags)
        asia = any(name == "Asia" and active for name, active in session_flags)

        forced_close = _bool(record.get("force_market_closed", False)) or _upper(record.get("market_status", ""), "") in {"CLOSED", "MARKET_CLOSED"}
        market_open = not weekend and not holiday and not forced_close
        market_closed = not market_open
        trading_allowed = market_open and not live
        if live:
            trading_block_reason = "live_execution_disabled"
        elif weekend:
            trading_block_reason = "weekend_market_closed"
        elif holiday:
            trading_block_reason = "holiday_market_closed"
        elif forced_close:
            trading_block_reason = "market_closed_by_runtime_input"
        else:
            trading_block_reason = "trading_allowed"

        if trading_allowed:
            status = "READY"
            reason = "market_open_and_trading_allowed_for_paper_or_demo_runtime"
            gate = "TRADING_ALLOWED"
            dashboard_status = f"OPEN / {primary_session} session"
        elif market_closed:
            status = "WAITING"
            reason = "market_calendar_waiting_until_market_open"
            gate = "TRADING_BLOCKED_BY_CALENDAR"
            dashboard_status = "CLOSED / calendar block"
        else:
            status = "BLOCKED"
            reason = "market_calendar_blocked_by_policy"
            gate = "TRADING_BLOCKED_BY_POLICY"
            dashboard_status = "BLOCKED / policy"

        next_review = (now + timedelta(minutes=15)).replace(second=0, microsecond=0)
        return MarketCalendarReport(
            status=status,
            reason=reason,
            broker=broker,
            symbol=symbol,
            market_open=market_open,
            market_closed=market_closed,
            weekend=weekend,
            holiday=holiday,
            holiday_name=holiday_name or "none",
            active_sessions=active_sessions,
            primary_session=primary_session,
            london_session=london,
            new_york_session=new_york,
            asia_session=asia,
            trading_allowed=trading_allowed,
            trading_block_reason=trading_block_reason,
            dashboard_market_status=dashboard_status,
            current_time_utc=now.isoformat(),
            next_review_time_utc=next_review.isoformat(),
            calendar_gate=gate,
            dashboard_message_th="แสดงสถานะตลาด ช่วงเวลาเทรด และเหตุผลที่อนุญาตหรือบล็อกการเทรดแบบอ่านอย่างเดียว",
            dashboard_message_en="Displays read-only market status, trading session, and trading permission reason.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )

    def explain_one(self, record: Mapping[str, Any] | None = None) -> MarketCalendarReport:
        return self.evaluate_one(record)

    def _blocked(self, reason: str, broker: str = VERSION1_BROKER, symbol: str = VERSION1_SYMBOL) -> MarketCalendarReport:
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        return MarketCalendarReport(
            status="BLOCKED",
            reason=reason,
            broker=broker,
            symbol=symbol,
            market_open=False,
            market_closed=True,
            weekend=False,
            holiday=False,
            holiday_name="none",
            active_sessions=(),
            primary_session="Blocked",
            london_session=False,
            new_york_session=False,
            asia_session=False,
            trading_allowed=False,
            trading_block_reason="live_execution_disabled" if "live" in reason else "version1_policy_blocked",
            dashboard_market_status="BLOCKED / policy",
            current_time_utc=now.isoformat(),
            next_review_time_utc=(now + timedelta(minutes=15)).isoformat(),
            calendar_gate="LIVE_EXECUTION_BLOCKED" if "live" in reason else "VERSION1_POLICY_BLOCKED",
            dashboard_message_th="บล็อกปฏิทินตลาดตามนโยบายความปลอดภัย Version 1",
            dashboard_message_en="Blocks market calendar telemetry according to Version 1 safety policy.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )
