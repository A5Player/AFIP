from afip.internet_monitor import InternetMonitorRuntime, InternetConnectivityReport
from afip.dashboard_ui import DashboardUIRuntime


def test_internet_monitor_reports_ready_with_latency_values():
    report = InternetMonitorRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "internet_status": "READY",
        "broker_status": "READY",
        "dns_status": "READY",
        "broker_latency_ms": 42.5,
        "dns_latency_ms": 12.0,
        "disconnect_count": 1,
        "reconnect_count": 1,
    })
    assert isinstance(report, InternetConnectivityReport)
    assert report.status == "READY"
    assert report.connection_gate == "INTERNET_CONNECTIVITY_READY"
    assert report.broker_latency_ms == 42.5
    assert report.live_execution_enabled is False
    assert report.trading_logic_changed is False


def test_internet_monitor_blocks_live_execution_policy():
    report = InternetMonitorRuntime().evaluate_one({"mode": "LIVE", "broker": "XM", "symbol": "GOLD#"})
    assert report.status == "BLOCKED"
    assert report.connection_gate == "LIVE_EXECUTION_BLOCKED"
    assert report.live_execution_enabled is False


def test_internet_monitor_blocks_non_xm_or_non_gold_version1_policy():
    broker_report = InternetMonitorRuntime().evaluate_one({"broker": "EXNESS", "symbol": "GOLD#"})
    symbol_report = InternetMonitorRuntime().evaluate_one({"broker": "XM", "symbol": "XAUUSD"})
    assert broker_report.status == "BLOCKED"
    assert symbol_report.status == "BLOCKED"
    assert broker_report.connection_gate == "VERSION1_POLICY_BLOCKED"
    assert symbol_report.connection_gate == "VERSION1_POLICY_BLOCKED"


def test_internet_monitor_waits_when_internet_or_broker_is_unavailable():
    report = InternetMonitorRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "internet_status": "WAITING",
        "broker_status": "WAITING",
        "dns_status": "WAITING",
    })
    assert report.status == "WAITING"
    assert report.connection_gate == "INTERNET_WAITING"


def test_internet_monitor_reviews_high_latency_and_disconnect_recovery():
    latency_report = InternetMonitorRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "internet_status": "READY",
        "broker_status": "READY",
        "dns_status": "READY",
        "broker_latency_ms": 900,
        "dns_latency_ms": 25,
        "latency_review_limit_ms": 750,
    })
    recovery_report = InternetMonitorRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "internet_status": "READY",
        "broker_status": "READY",
        "dns_status": "READY",
        "broker_latency_ms": 20,
        "dns_latency_ms": 10,
        "disconnect_count": 3,
        "reconnect_count": 2,
        "disconnect_duration_seconds": 60,
    })
    assert latency_report.status == "REVIEW"
    assert latency_report.connection_gate == "LATENCY_REVIEW"
    assert recovery_report.status == "REVIEW"
    assert recovery_report.connection_gate == "RECOVERY_REVIEW"


def test_dashboard_system_and_internet_panel_use_live_connectivity_values():
    report = DashboardUIRuntime().evaluate_one({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "production_readiness_requested": True,
        "internet_status": "READY",
        "broker_status": "READY",
        "dns_status": "READY",
        "broker_latency_ms": 44,
        "dns_latency_ms": 11,
        "disconnect_count": 2,
        "reconnect_count": 2,
    })
    panels = {panel.panel_id: panel for panel in report.panels}
    assert "internet_monitor" in panels
    assert ("Broker Latency", "44.0 ms") in panels["internet_monitor"].rows
    assert ("Internet Latency", "11.0 ms") in panels["system"].rows
    assert ("Disconnect Count", "2") in panels["system"].rows
    assert report.live_execution_enabled is False


def test_dashboard_html_renders_internet_monitor_without_enabling_live_execution():
    html = DashboardUIRuntime().render_html({
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "production_readiness_requested": True,
        "internet_status": "READY",
        "broker_status": "READY",
        "dns_status": "READY",
        "broker_latency_ms": 33,
        "dns_latency_ms": 9,
    })
    assert "Internet Monitor" in html
    assert "ตัวตรวจสอบอินเทอร์เน็ต" in html
    assert "33.0 ms" in html
    assert "Live Execution: False" in html
