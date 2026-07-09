from afip.dashboard_ui import DashboardUIRuntime
from afip.mt5_live_account import MT5LiveAccountRuntime


def _ready_record():
    return {
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "production_readiness_requested": True,
        "mt5_account_info": {
            "available": True,
            "login": 12345678,
            "server": "XMGlobal-MT5 5",
            "name": "AFIP VPS Demo",
            "balance": 1000.0,
            "equity": 1003.5,
            "margin": 10.0,
            "free_margin": 993.5,
            "leverage": "1:500",
            "currency": "USD",
        },
        "mt5_tick": {"available": True, "bid": 2300.10, "ask": 2300.34, "time": "2026-07-09T16:00:00Z"},
        "mt5_symbol_info": {"available": True, "point": 0.01, "digits": 2},
    }


def test_mt5_live_account_reports_ready_read_only_account_values():
    report = MT5LiveAccountRuntime().evaluate_one(_ready_record())

    assert report.status == "READY"
    assert report.reason == "mt5_live_account_ready"
    assert report.server == "XMGlobal-MT5 5"
    assert report.login == "****5678"
    assert report.balance == 1000.0
    assert report.equity == 1003.5
    assert report.spread_points == 24.0
    assert report.trading_logic_changed is False
    assert report.live_execution_enabled is False


def test_mt5_live_account_blocks_live_execution_policy():
    record = {**_ready_record(), "mode": "LIVE", "live_execution_enabled": True}
    report = MT5LiveAccountRuntime().evaluate_one(record)

    assert report.status == "BLOCKED"
    assert report.reason == "live_execution_blocked_for_mt5_live_account"
    assert report.account_gate == "LIVE_EXECUTION_BLOCKED"
    assert report.live_execution_enabled is False


def test_mt5_live_account_blocks_non_xm_or_non_gold_version1_policy():
    non_xm = MT5LiveAccountRuntime().evaluate_one({**_ready_record(), "broker": "EXNESS"})
    non_gold = MT5LiveAccountRuntime().evaluate_one({**_ready_record(), "symbol": "EURUSD"})

    assert non_xm.status == "BLOCKED"
    assert non_xm.reason == "version1_xm_only_required_for_mt5_live_account"
    assert non_gold.status == "BLOCKED"
    assert non_gold.reason == "version1_gold_only_required_for_mt5_live_account"


def test_mt5_live_account_waits_for_account_or_tick_when_not_available():
    account_waiting = MT5LiveAccountRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "DEMO"})
    tick_waiting = MT5LiveAccountRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "mt5_account_info": {"available": True, "server": "XMGlobal-MT5 5", "login": 1234},
        "mt5_tick": {"available": False, "reason": "tick_unavailable"},
    })

    assert account_waiting.status == "WAITING"
    assert account_waiting.reason == "mt5_live_account_not_requested"
    assert tick_waiting.status == "WAITING"
    assert tick_waiting.reason == "tick_unavailable"


def test_mt5_live_account_reviews_spread_pressure_without_blocking():
    record = _ready_record()
    record["mt5_tick"] = {"available": True, "bid": 2300.10, "ask": 2300.80, "time": "2026-07-09T16:00:00Z"}
    report = MT5LiveAccountRuntime().evaluate_one(record)

    assert report.status == "REVIEW"
    assert report.reason == "mt5_spread_review_required"
    assert report.account_gate == "MT5_SPREAD_REVIEW"


def test_dashboard_system_and_mt5_account_panel_use_live_account_values():
    report = DashboardUIRuntime().evaluate_one(_ready_record())
    panels = {panel.panel_id: panel for panel in report.panels}

    assert "mt5_account" in panels
    mt5_rows = dict(panels["mt5_account"].rows)
    system_rows = dict(panels["system"].rows)
    assert panels["mt5_account"].status == "READY"
    assert mt5_rows["Server"] == "XMGlobal-MT5 5"
    assert mt5_rows["Equity"] == "1003.5"
    assert mt5_rows["Spread"] == "24.0 pts"
    assert system_rows["MT5 Account"] == "READY"
    assert system_rows["MT5 Server"] == "XMGlobal-MT5 5"


def test_dashboard_html_renders_mt5_live_account_without_enabling_live_execution(tmp_path):
    output_path = tmp_path / "afip_dashboard.html"
    path = DashboardUIRuntime().write_html(_ready_record(), output_path)
    html = path.read_text(encoding="utf-8")

    assert "MT5 Live Account" in html
    assert "XMGlobal-MT5 5" in html
    assert "1003.5" in html
    assert "Live Execution: False" in html
