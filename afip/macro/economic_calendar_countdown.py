"""Countdown assessment for upcoming economic calendar events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from afip.macro.economic_calendar_runtime import EconomicCalendarEvent


@dataclass(frozen=True)
class EconomicCalendarCountdown:
    """Time-distance view of the next macro event."""

    status: str
    next_event: str | None
    minutes_to_event: float | None
    countdown_label: str
    phase: str
    trade_instruction: str
    reason: str


class EconomicCalendarCountdownEngine:
    """Classify the event countdown into clear trading review phases."""

    def __init__(self, pre_event_minutes: int = 30, post_event_minutes: int = 15) -> None:
        self.pre_event_minutes = int(pre_event_minutes)
        self.post_event_minutes = int(post_event_minutes)

    def assess(self, event: EconomicCalendarEvent | None, now: datetime | None = None) -> EconomicCalendarCountdown:
        current_time = self._ensure_timezone(now or datetime.now(timezone.utc))
        if event is None:
            return EconomicCalendarCountdown(
                status="CALENDAR_COUNTDOWN_CLEAR",
                next_event=None,
                minutes_to_event=None,
                countdown_label="NO_EVENT",
                phase="CLEAR",
                trade_instruction="NORMAL_REVIEW",
                reason="no_upcoming_calendar_event",
            )
        event_time = self._ensure_timezone(event.scheduled_at)
        minutes_to_event = (event_time - current_time).total_seconds() / 60.0
        countdown_label = self._format_label(minutes_to_event)
        if 0 <= minutes_to_event <= self.pre_event_minutes:
            phase = "PRE_EVENT_RESTRICTED"
            instruction = "NO_NEW_POSITION"
            reason = "inside_pre_event_restricted_window"
        elif -self.post_event_minutes <= minutes_to_event < 0:
            phase = "POST_EVENT_REVIEW"
            instruction = "WAIT_VOLATILITY"
            reason = "inside_post_event_review_window"
        elif self.pre_event_minutes < minutes_to_event <= self.pre_event_minutes + 30:
            phase = "PRE_EVENT_ELEVATED"
            instruction = "REDUCE_NEW_EXPOSURE"
            reason = "approaching_high_impact_event"
        else:
            phase = "CLEAR"
            instruction = "NORMAL_REVIEW"
            reason = "outside_restricted_calendar_window"
        return EconomicCalendarCountdown(
            status="CALENDAR_COUNTDOWN_READY",
            next_event=event.name,
            minutes_to_event=round(minutes_to_event, 2),
            countdown_label=countdown_label,
            phase=phase,
            trade_instruction=instruction,
            reason=reason,
        )

    def assess_dict(self, event: EconomicCalendarEvent | None, now: datetime | None = None) -> dict[str, object]:
        result = self.assess(event, now)
        return {
            "status": result.status,
            "next_event": result.next_event,
            "minutes_to_event": result.minutes_to_event,
            "countdown_label": result.countdown_label,
            "phase": result.phase,
            "trade_instruction": result.trade_instruction,
            "reason": result.reason,
        }

    def _format_label(self, minutes_to_event: float) -> str:
        total_seconds = int(abs(minutes_to_event) * 60)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        prefix = "T-" if minutes_to_event >= 0 else "T+"
        return f"{prefix}{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _ensure_timezone(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
