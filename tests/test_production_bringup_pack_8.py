from afip.dashboard_live_runtime import DashboardLiveRuntime
from afip.dashboard_ui import DashboardUIRuntime


def test_dashboard_live_runtime_reports_fresh_refresh_ready():
    report = DashboardLiveRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "dashboard_data_age_seconds": 4})
    assert report.status == "READY"
    assert report.runtime_state == "RUNNING"
    assert report.data_state == "FRESH"
    assert report.live_execution_enabled is False


def test_dashboard_live_runtime_marks_stale_snapshot_for_review():
    report = DashboardLiveRuntime().evaluate_one({"dashboard_data_age_seconds": 31, "dashboard_stale_after_seconds": 30})
    assert report.status == "REVIEW"
    assert report.data_fresh is False
    assert "stale" in report.reason


def test_dashboard_live_runtime_waits_when_launcher_disabled():
    report = DashboardLiveRuntime().evaluate_one({"dashboard_live_runtime_enabled": False})
    assert report.status == "WAITING"
    assert report.runtime_state == "STOPPED"


def test_dashboard_live_runtime_blocks_live_execution_and_version_policy():
    assert DashboardLiveRuntime().evaluate_one({"live_execution_enabled": True}).status == "BLOCKED"
    assert DashboardLiveRuntime().evaluate_one({"broker": "EXNESS"}).status == "BLOCKED"
    assert DashboardLiveRuntime().evaluate_one({"symbol": "EURUSD"}).status == "BLOCKED"


def test_dashboard_live_runtime_explanations_are_bilingual():
    report = DashboardLiveRuntime().explain_one({})
    assert report.waiting_reason_en
    assert report.waiting_reason_th
    assert report.expected_next_action_en
    assert report.expected_next_action_th


def test_dashboard_renders_dashboard_live_runtime_panel_without_navigation_regression():
    runtime = DashboardUIRuntime()
    report = runtime.evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    panel = next(panel for panel in report.panels if panel.panel_id == "dashboard_live_runtime")
    assert panel.status == "READY"
    assert "Runtime" in report.navigation_sections
    html = runtime.render_html({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "Dashboard Live Runtime" in html
    assert "ระบบ Dashboard แบบสด" in html
    assert "Live Execution</td><td>False" in html
