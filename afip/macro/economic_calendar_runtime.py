"""Economic calendar runtime for high-impact macro events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping

HIGH_IMPACT_EVENTS = {
    "FOMC",
    "FED_RATE_DECISION",
    "FED_CHAIR_SPEECH",
    "CPI",
    "CORE_CPI",
    "PCE",
    "CORE_PCE",
    "NFP",
    "NONFARM_PAYROLLS",
    "JOBLESS_CLAIMS",
    "GDP",
    "PPI",
    "RETAIL_SALES",
    "ISM",
    "PMI",
}


@dataclass(frozen=True)
class EconomicCalendarEvent:
    """Normalized economic calendar event."""

    name: str
    currency: str
    impact: str
    scheduled_at: datetime
    forecast: float | None = None
    previous: float | None = None
    actual: float | None = None

    @property
    def normalized_name(self) -> str:
        return self.name.strip().upper().replace(" ", "_").replace("-", "_")


class EconomicCalendarRuntime:
    """Normalize macro calendar data and select the next relevant event."""

    def __init__(self, pre_event_minutes: int = 30, post_event_minutes: int = 15) -> None:
        self.pre_event_minutes = int(pre_event_minutes)
        self.post_event_minutes = int(post_event_minutes)

    def normalize(self, raw_events: Iterable[Mapping[str, object]]) -> tuple[EconomicCalendarEvent, ...]:
        events: list[EconomicCalendarEvent] = []
        for raw in raw_events:
            scheduled_at = self._parse_time(raw.get("scheduled_at") or raw.get("time"))
            if scheduled_at is None:
                continue
            events.append(
                EconomicCalendarEvent(
                    name=str(raw.get("name", "")).strip(),
                    currency=str(raw.get("currency", "USD")).upper(),
                    impact=str(raw.get("impact", "LOW")).upper(),
                    scheduled_at=scheduled_at,
                    forecast=self._to_float(raw.get("forecast")),
                    previous=self._to_float(raw.get("previous")),
                    actual=self._to_float(raw.get("actual")),
                )
            )
        return tuple(sorted(events, key=lambda event: event.scheduled_at))

    def next_event(self, events: Iterable[EconomicCalendarEvent], now: datetime | None = None) -> EconomicCalendarEvent | None:
        current_time = self._ensure_timezone(now or datetime.now(timezone.utc))
        future_events = [event for event in events if self._ensure_timezone(event.scheduled_at) >= current_time]
        return future_events[0] if future_events else None

    def runtime_state(self, raw_events: Iterable[Mapping[str, object]], now: datetime | None = None) -> dict[str, object]:
        events = self.normalize(raw_events)
        current_time = self._ensure_timezone(now or datetime.now(timezone.utc))
        next_macro_event = self.next_event(events, current_time)
        if next_macro_event is None:
            return {
                "status": "MACRO_CALENDAR_READY",
                "event_count": len(events),
                "next_event": None,
                "minutes_to_event": None,
                "event_risk_state": "CLEAR",
                "trade_instruction": "NORMAL_REVIEW",
            }

        event_time = self._ensure_timezone(next_macro_event.scheduled_at)
        minutes_to_event = (event_time - current_time).total_seconds() / 60.0
        normalized_name = next_macro_event.normalized_name
        high_impact = next_macro_event.impact == "HIGH" or normalized_name in HIGH_IMPACT_EVENTS

        if high_impact and -self.post_event_minutes <= minutes_to_event <= self.pre_event_minutes:
            event_risk_state = "RESTRICTED"
            trade_instruction = "NO_NEW_POSITION"
        elif high_impact and 0 <= minutes_to_event <= self.pre_event_minutes + 30:
            event_risk_state = "ELEVATED"
            trade_instruction = "REDUCE_NEW_EXPOSURE"
        else:
            event_risk_state = "CLEAR"
            trade_instruction = "NORMAL_REVIEW"

        return {
            "status": "MACRO_CALENDAR_READY",
            "event_count": len(events),
            "next_event": next_macro_event.name,
            "next_event_currency": next_macro_event.currency,
            "next_event_impact": next_macro_event.impact,
            "minutes_to_event": round(minutes_to_event, 2),
            "event_risk_state": event_risk_state,
            "trade_instruction": trade_instruction,
        }

    def _parse_time(self, value: object) -> datetime | None:
        if isinstance(value, datetime):
            return self._ensure_timezone(value)
        if isinstance(value, str) and value.strip():
            text = value.strip().replace("Z", "+00:00")
            try:
                return self._ensure_timezone(datetime.fromisoformat(text))
            except ValueError:
                return None
        return None

    def _ensure_timezone(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _to_float(self, value: object) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
