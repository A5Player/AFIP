"""Production Bring-up Pack 1 — VPS Health Monitor tests."""

from __future__ import annotations

from afip.dashboard_ui import DashboardUIRuntime
from afip.vps_health_monitor import VPSHealthMonitorRuntime


def _record(**overrides):
    base = {
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "execution_mode": "DEMO",
        "profile_name": "Balanced",
        "internet_status": "CONNECTED",
        "mt5_status": "CONNECTED",
        "broker_status": "XM_READY",
        "connection_test_passed": True,
        "saved": True,
        "login": "configured",
        "password": "configured",
        "mt5_terminal_path": "configured",
        "historical_data_ready": True,
        "history_ready": True,
        "historical_research_ready": True,
        "walk_forward_ready": True,
        "research_center_requested": True,
        "completed_research_orders": 120,
        "paper_trading_requested": True,
        "demo_trading_requested": True,
        "production_readiness_requested": True,
        "vps_ready": True,
        "windows_vps_ready": True,
        "market_regime": "TRENDING",
        "market_status": "OPEN",
        "trading_session": "London",
        "hostname": "DESKTOP-CLPP7LQ",
        "windows_version": "10.0.19045",
        "operating_system": "Windows",
        "architecture": "AMD64",
        "python_version": "3.14.6",
        "uptime_seconds": 7200,
        "cpu_percent": 14.0,
        "ram_percent": 37.0,
        "disk_total_gb": 80.0,
        "disk_free_gb": 64.0,
    }
    base.update(overrides)
    return base


def test_vps_health_monitor_reports_ready_without_trading_logic_change():
    report = VPSHealthMonitorRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.reason == "vps_health_ready"
    assert report.hostname == "DESKTOP-CLPP7LQ"
    assert report.cpu_percent == 14.0
    assert report.ram_percent == 37.0
    assert report.disk_percent == 20.0
    assert report.trading_logic_changed is False
    assert report.live_execution_enabled is False


def test_vps_health_monitor_blocks_live_execution_policy():
    report = VPSHealthMonitorRuntime().evaluate_one(_record(mode="LIVE", live_execution_enabled=True))
    assert report.status == "BLOCKED"
    assert report.reason == "live_execution_blocked_for_vps_health_monitor"
    assert report.health_gate == "LIVE_EXECUTION_BLOCKED"
    assert report.live_execution_enabled is False


def test_vps_health_monitor_reviews_resource_pressure():
    report = VPSHealthMonitorRuntime().evaluate_one(_record(cpu_percent=96.0, ram_percent=40.0, disk_free_gb=64.0))
    assert report.status == "REVIEW"
    assert report.reason == "vps_resource_pressure_review_required"
    assert report.health_gate == "VPS_HEALTH_REVIEW"


def test_vps_health_monitor_contains_thai_and_english_dashboard_messages():
    report = VPSHealthMonitorRuntime().evaluate_one(_record())
    assert "Windows VPS" in report.dashboard_message_th
    assert "Windows VPS health" in report.dashboard_message_en
    assert "AFIP VPS Health Monitor" in report.as_text()


def test_dashboard_system_panel_uses_live_vps_health_values():
    report = DashboardUIRuntime().evaluate_one(_record())
    panel = next(panel for panel in report.panels if panel.panel_id == "system")
    rows = dict(panel.rows)
    assert panel.status == "READY"
    assert rows["VPS Health"] == "READY"
    assert rows["Hostname"] == "DESKTOP-CLPP7LQ"
    assert rows["CPU"] == "14.0%"
    assert rows["RAM"] == "37.0%"
    assert rows["Disk"] == "20.0% used / 64.0 GB free"


def test_dashboard_html_renders_vps_health_without_enabling_live_execution():
    html = DashboardUIRuntime().render_html(_record())
    report = DashboardUIRuntime().evaluate_one(_record())
    assert "VPS Health" in html
    assert "14.0%" in html
    assert "Live Execution: False" in html
    assert report.trading_logic_changed is False
    assert report.live_execution_enabled is False


def test_vps_health_monitor_is_available_from_public_exports():
    report = VPSHealthMonitorRuntime().explain_one(_record())
    data = report.as_dict()
    assert data["status"] == "READY"
    assert data["health_gate"] == "VPS_HEALTH_READY"
    assert data["trading_logic_changed"] is False
