from afip.economic_calendar_intelligence import EconomicCalendarIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime

BASE={"broker":"XM","symbol":"GOLD#","mode":"PAPER","current_time_utc":"2026-07-10T12:00:00+00:00"}

def test_high_impact_usd_gold_event_blocks_inside_window():
    r=EconomicCalendarIntelligenceRuntime().evaluate_one({**BASE,"economic_events":[{"title":"US CPI","currency":"USD","impact":"HIGH","scheduled_time_utc":"2026-07-10T12:20:00+00:00"}]})
    assert r.status=="CAUTION" and not r.trading_allowed and r.events[0].gold_relevance=="HIGH"

def test_high_impact_event_outside_window_does_not_block():
    r=EconomicCalendarIntelligenceRuntime().evaluate_one({**BASE,"economic_events":[{"title":"FOMC Rate Decision","currency":"USD","impact":"HIGH","scheduled_time_utc":"2026-07-10T14:00:00+00:00"}]})
    assert r.status=="READY" and r.trading_allowed and r.events[0].event_window=="UPCOMING"

def test_event_classification_is_deterministic():
    e=EconomicCalendarIntelligenceRuntime().evaluate_one({**BASE,"economic_events":[{"title":"Nonfarm Payrolls","currency":"USD","impact":"HIGH","scheduled_time_utc":"2026-07-10T13:00:00+00:00"}]}).events[0]
    assert e.event_category=="EMPLOYMENT" and e.minutes_until_event==60

def test_version_policy_remains_xm_gold_only_and_live_disabled():
    r=EconomicCalendarIntelligenceRuntime().evaluate_one({**BASE,"broker":"OTHER","live_execution_enabled":True})
    assert r.status=="BLOCKED" and not r.live_execution_enabled and not r.trading_allowed

def test_news_never_executes_directly():
    r=EconomicCalendarIntelligenceRuntime().evaluate_one(BASE)
    assert r.event_count==0 and r.trading_block_reason=="economic_calendar_pass"

def test_dashboard_contains_bilingual_economic_calendar_panel():
    html=DashboardUIRuntime().render_html({**BASE,"economic_events":[{"title":"US CPI","currency":"USD","impact":"HIGH","scheduled_time_utc":"2026-07-10T12:20:00+00:00"}]})
    assert "Economic Calendar Intelligence" in html and "ปัญญาปฏิทินเศรษฐกิจ" in html and "US CPI" in html
