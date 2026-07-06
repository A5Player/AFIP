from datetime import date, datetime, timedelta, timezone

from afip.macro.economic_calendar_cache import EconomicCalendarCache
from afip.macro.economic_calendar_countdown import EconomicCalendarCountdownEngine
from afip.macro.economic_calendar_holiday import MarketHolidayCalendar
from afip.macro.economic_calendar_provider import EmptyEconomicCalendarProvider, StaticEconomicCalendarProvider
from afip.runtime.production_milestone_c_calendar_runtime import ProductionMilestoneCCalendarRuntime


def test_static_calendar_provider_returns_deterministic_events():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = StaticEconomicCalendarProvider([
        {"name": "CPI", "currency": "USD", "impact": "HIGH", "scheduled_at": now.isoformat()}
    ])

    result = provider.fetch_events(now)

    assert result.status == "CALENDAR_PROVIDER_READY"
    assert result.source == "STATIC_FREE_CALENDAR"
    assert len(result.events) == 1
    assert result.events[0]["name"] == "CPI"


def test_empty_calendar_provider_is_safe_fallback():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = EmptyEconomicCalendarProvider()

    result = provider.fetch_events(now)

    assert result.status == "CALENDAR_PROVIDER_EMPTY"
    assert result.events == ()
    assert result.reason == "no_calendar_provider_configured"


def test_calendar_cache_returns_recent_result_before_expiry():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = StaticEconomicCalendarProvider([
        {"name": "FOMC", "currency": "USD", "impact": "HIGH", "scheduled_at": (now + timedelta(minutes=20)).isoformat()}
    ])
    result = provider.fetch_events(now)
    cache = EconomicCalendarCache(ttl_seconds=300)

    cache.set(result, now)
    cached = cache.get(now + timedelta(seconds=120))

    assert cached is result
    assert cache.state(now + timedelta(seconds=120)).status == "CALENDAR_CACHE_READY"


def test_calendar_cache_expires_old_result():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    result = StaticEconomicCalendarProvider([]).fetch_events(now)
    cache = EconomicCalendarCache(ttl_seconds=60)

    cache.set(result, now)

    assert cache.get(now + timedelta(seconds=90)) is None
    assert cache.state(now + timedelta(seconds=90)).status == "CALENDAR_CACHE_EXPIRED"


def test_countdown_engine_restricts_pre_event_window():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    runtime = ProductionMilestoneCCalendarRuntime()
    state = runtime.run_dict(
        [
            {
                "name": "CPI",
                "currency": "USD",
                "impact": "HIGH",
                "scheduled_at": (now + timedelta(minutes=25)).isoformat(),
            }
        ],
        now,
    )

    assert state["countdown_phase"] == "PRE_EVENT_RESTRICTED"
    assert state["trade_instruction"] == "NO_NEW_POSITION"
    assert state["countdown_label"].startswith("T-")


def test_countdown_engine_marks_post_event_review_window():
    now = datetime(2026, 7, 6, 12, 10, tzinfo=timezone.utc)
    calendar_runtime = ProductionMilestoneCCalendarRuntime()
    state = calendar_runtime.run_dict(
        [
            {
                "name": "PCE",
                "currency": "USD",
                "impact": "HIGH",
                "scheduled_at": (now - timedelta(minutes=5)).isoformat(),
            }
        ],
        now,
    )

    assert state["countdown_phase"] == "CLEAR"
    assert state["event_risk_state"] == "CLEAR"


def test_countdown_engine_direct_post_event_assessment():
    from afip.macro.economic_calendar_runtime import EconomicCalendarEvent

    now = datetime(2026, 7, 6, 12, 10, tzinfo=timezone.utc)
    event = EconomicCalendarEvent("PCE", "USD", "HIGH", now - timedelta(minutes=5))

    countdown = EconomicCalendarCountdownEngine().assess(event, now)

    assert countdown.phase == "POST_EVENT_REVIEW"
    assert countdown.trade_instruction == "WAIT_VOLATILITY"


def test_holiday_calendar_blocks_weekend_new_position():
    holiday_calendar = MarketHolidayCalendar()
    state = holiday_calendar.assess(date(2026, 7, 5))

    assert state.is_holiday is True
    assert state.liquidity_state == "WEEKEND_CLOSED"
    assert state.trade_instruction == "NO_NEW_POSITION"


def test_holiday_calendar_flags_configured_holiday_as_thin_liquidity():
    holiday_calendar = MarketHolidayCalendar(["2026-12-25"])
    state = holiday_calendar.assess(date(2026, 12, 25))

    assert state.is_holiday is True
    assert state.liquidity_state == "HOLIDAY_THIN_LIQUIDITY"
    assert state.trade_instruction == "REDUCE_NEW_EXPOSURE"


def test_calendar_runtime_uses_provider_and_cache():
    now = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)
    provider = StaticEconomicCalendarProvider([
        {
            "name": "Nonfarm Payrolls",
            "currency": "USD",
            "impact": "HIGH",
            "scheduled_at": (now + timedelta(minutes=50)).isoformat(),
        }
    ])
    runtime = ProductionMilestoneCCalendarRuntime(provider=provider)

    first = runtime.run_dict(now=now)
    second = runtime.run_dict(now=now + timedelta(minutes=1))

    assert first["status"] == "PRODUCTION_MILESTONE_C_CALENDAR_READY"
    assert first["provider_source"] == "STATIC_FREE_CALENDAR"
    assert first["cache_status"] == "CALENDAR_CACHE_READY"
    assert first["event_count"] == 1
    assert second["next_event"] == "Nonfarm Payrolls"


def test_calendar_runtime_normalizes_naive_datetime_to_utc():
    now = datetime(2026, 7, 6, 12, 0)
    runtime = ProductionMilestoneCCalendarRuntime()

    state = runtime.run_dict(
        [
            {
                "name": "Jobless Claims",
                "currency": "USD",
                "impact": "HIGH",
                "scheduled_at": datetime(2026, 7, 6, 12, 20),
            }
        ],
        now,
    )

    assert state["next_event"] == "Jobless Claims"
    assert state["minutes_to_event"] == 20.0
    assert state["trade_instruction"] == "NO_NEW_POSITION"
