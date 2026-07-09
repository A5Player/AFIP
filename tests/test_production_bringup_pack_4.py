from afip.market_calendar import MarketCalendarRuntime, MarketCalendarReport
from afip.dashboard_ui import DashboardUIRuntime


def test_market_calendar_reports_london_new_york_overlap_as_trading_allowed():
    report = MarketCalendarRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "current_time_utc": "2026-07-10T14:30:00+00:00",
    })
    assert isinstance(report, MarketCalendarReport)
    assert report.status == "READY"
    assert report.market_open is True
    assert report.trading_allowed is True
    assert report.trading_block_reason == "trading_allowed"
    assert report.london_session is True
    assert report.new_york_session is True
    assert report.asia_session is False
    assert report.primary_session == "New York"
    assert report.live_execution_enabled is False
    assert report.trading_logic_changed is False


def test_market_calendar_blocks_weekend_before_gold_reopen():
    report = MarketCalendarRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "current_time_utc": "2026-07-12T12:00:00+00:00",
    })
    assert report.status == "WAITING"
    assert report.market_closed is True
    assert report.weekend is True
    assert report.trading_allowed is False
    assert report.trading_block_reason == "weekend_market_closed"
    assert report.calendar_gate == "TRADING_BLOCKED_BY_CALENDAR"


def test_market_calendar_blocks_configured_holiday():
    report = MarketCalendarRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "PAPER",
        "current_time_utc": "2026-07-10T09:00:00+00:00",
        "holiday_calendar": {"2026-07-10": "Configured gold market holiday"},
    })
    assert report.status == "WAITING"
    assert report.holiday is True
    assert report.holiday_name == "Configured gold market holiday"
    assert report.trading_allowed is False
    assert report.trading_block_reason == "holiday_market_closed"


def test_market_calendar_blocks_live_execution_and_version_policy():
    live_report = MarketCalendarRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "LIVE"})
    broker_report = MarketCalendarRuntime().evaluate_one({"broker": "EXNESS", "symbol": "GOLD#"})
    symbol_report = MarketCalendarRuntime().evaluate_one({"broker": "XM", "symbol": "XAUUSD"})
    assert live_report.status == "BLOCKED"
    assert live_report.calendar_gate == "LIVE_EXECUTION_BLOCKED"
    assert broker_report.status == "BLOCKED"
    assert symbol_report.status == "BLOCKED"
    assert broker_report.calendar_gate == "VERSION1_POLICY_BLOCKED"
    assert symbol_report.calendar_gate == "VERSION1_POLICY_BLOCKED"


def test_dashboard_renders_market_calendar_panel_with_block_reason():
    report = DashboardUIRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "production_readiness_requested": True,
        "current_time_utc": "2026-07-12T12:00:00+00:00",
    })
    panels = {panel.panel_id: panel for panel in report.panels}
    assert "market_calendar" in panels
    rows = dict(panels["market_calendar"].rows)
    assert rows["Market Open"] == "False"
    assert rows["Weekend"] == "True"
    assert rows["Trading Allowed"] == "False"
    assert rows["Trading Block Reason"] == "weekend_market_closed"
    assert dict(panels["market"].rows)["Trading Block Reason"] == "weekend_market_closed"
    assert report.live_execution_enabled is False


def test_dashboard_html_contains_live_market_status_explainability():
    html = DashboardUIRuntime().render_html({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "production_readiness_requested": True,
        "current_time_utc": "2026-07-10T14:30:00+00:00",
    })
    assert "Market Session &amp; Trading Calendar" in html
    assert "ปฏิทินตลาดและช่วงเวลาเทรด" in html
    assert "Trading Block Reason" in html
    assert "Dashboard Live Market Status" in html
    assert "OPEN / New York session" in html
    assert "Live Execution: False" in html
