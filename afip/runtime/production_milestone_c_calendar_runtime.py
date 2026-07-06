"""Production Milestone C Pack 2 economic calendar integration runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping

from afip.macro.economic_calendar_cache import EconomicCalendarCache
from afip.macro.economic_calendar_countdown import EconomicCalendarCountdownEngine
from afip.macro.economic_calendar_holiday import MarketHolidayCalendar
from afip.macro.economic_calendar_provider import EconomicCalendarProvider, StaticEconomicCalendarProvider
from afip.macro.economic_calendar_runtime import EconomicCalendarRuntime


@dataclass(frozen=True)
class ProductionMilestoneCCalendarRuntimeResult:
    """Pack 2 integrated economic calendar runtime result."""

    status: str
    ready: bool
    provider_status: str
    provider_source: str
    cache_status: str
    event_count: int
    next_event: str | None
    next_event_currency: str | None
    next_event_impact: str | None
    countdown_label: str
    countdown_phase: str
    minutes_to_event: float | None
    event_risk_state: str
    holiday_state: str
    trade_instruction: str
    reason: str


class ProductionMilestoneCCalendarRuntime:
    """Integrate provider, cache, countdown, timezone and holiday calendar checks."""

    def __init__(
        self,
        provider: EconomicCalendarProvider | None = None,
        cache: EconomicCalendarCache | None = None,
        holiday_calendar: MarketHolidayCalendar | None = None,
    ) -> None:
        self.provider = provider or StaticEconomicCalendarProvider(())
        self.cache = cache or EconomicCalendarCache(ttl_seconds=300)
        self.calendar_runtime = EconomicCalendarRuntime()
        self.countdown_engine = EconomicCalendarCountdownEngine()
        self.holiday_calendar = holiday_calendar or MarketHolidayCalendar()

    def run(
        self,
        economic_events: Iterable[Mapping[str, object]] | None = None,
        now: datetime | None = None,
    ) -> ProductionMilestoneCCalendarRuntimeResult:
        current_time = self._ensure_timezone(now or datetime.now(timezone.utc))
        if economic_events is not None:
            provider = StaticEconomicCalendarProvider(economic_events, source="INLINE_CALENDAR_EVENTS")
        else:
            provider = self.provider
        provider_result = provider.fetch_events(current_time)
        resolved_result = self.cache.resolve(provider_result, current_time) or provider_result
        cache_state = self.cache.state(current_time)
        events = self.calendar_runtime.normalize(resolved_result.events)
        next_event = self.calendar_runtime.next_event(events, current_time)
        calendar_state = self.calendar_runtime.runtime_state(resolved_result.events, current_time)
        countdown = self.countdown_engine.assess(next_event, current_time)
        holiday_state = self.holiday_calendar.assess(current_time)
        trade_instruction = self._select_trade_instruction(
            str(calendar_state.get("trade_instruction", "NORMAL_REVIEW")),
            countdown.trade_instruction,
            holiday_state.trade_instruction,
        )
        reason = self._select_reason(str(calendar_state.get("event_risk_state", "CLEAR")), countdown.reason, holiday_state.reason)
        return ProductionMilestoneCCalendarRuntimeResult(
            status="PRODUCTION_MILESTONE_C_CALENDAR_READY",
            ready=True,
            provider_status=resolved_result.status,
            provider_source=resolved_result.source,
            cache_status=cache_state.status,
            event_count=len(events),
            next_event=calendar_state.get("next_event"),
            next_event_currency=calendar_state.get("next_event_currency"),
            next_event_impact=calendar_state.get("next_event_impact"),
            countdown_label=countdown.countdown_label,
            countdown_phase=countdown.phase,
            minutes_to_event=calendar_state.get("minutes_to_event"),
            event_risk_state=str(calendar_state.get("event_risk_state", "CLEAR")),
            holiday_state=holiday_state.liquidity_state,
            trade_instruction=trade_instruction,
            reason=reason,
        )

    def run_dict(
        self,
        economic_events: Iterable[Mapping[str, object]] | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        return asdict(self.run(economic_events, now))

    def _select_trade_instruction(self, calendar_instruction: str, countdown_instruction: str, holiday_instruction: str) -> str:
        priority = {
            "NORMAL_REVIEW": 0,
            "REDUCE_NEW_EXPOSURE": 1,
            "WAIT_VOLATILITY": 2,
            "NO_NEW_POSITION": 3,
        }
        instructions = (calendar_instruction, countdown_instruction, holiday_instruction)
        return max(instructions, key=lambda instruction: priority.get(instruction, 0))

    def _select_reason(self, event_risk_state: str, countdown_reason: str, holiday_reason: str) -> str:
        if holiday_reason != "no_holiday_restriction":
            return holiday_reason
        if event_risk_state in {"RESTRICTED", "ELEVATED"}:
            return countdown_reason
        return "calendar_integration_ready"

    def _ensure_timezone(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
