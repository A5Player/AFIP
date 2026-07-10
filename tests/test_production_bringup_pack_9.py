from afip.dashboard_ui import DashboardUIRuntime
from afip.runtime_supervisor import RuntimeSupervisorRuntime


def test_runtime_supervisor_reports_all_dependencies_healthy():
    report = RuntimeSupervisorRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#"})
    assert report.status == "READY"
    assert report.runtime_health == "HEALTHY"
    assert report.healthy_modules == 7
    assert report.live_execution_enabled is False


def test_runtime_supervisor_reports_warning_without_unlocking_execution():
    report = RuntimeSupervisorRuntime().evaluate_one({"internet_status": "CAUTION"})
    assert report.status == "REVIEW"
    assert report.warning_modules == 1
    assert "internet" in report.warning_modules_list
    assert report.live_execution_enabled is False


def test_runtime_supervisor_blocks_critical_dependency():
    report = RuntimeSupervisorRuntime().evaluate_one({"mt5_status": "FAILED"})
    assert report.status == "BLOCKED"
    assert report.runtime_health == "CRITICAL"
    assert "mt5" in report.critical_modules_list


def test_runtime_supervisor_blocks_version1_and_live_policy():
    runtime = RuntimeSupervisorRuntime()
    assert runtime.evaluate_one({"broker": "EXNESS"}).status == "BLOCKED"
    assert runtime.evaluate_one({"symbol": "EURUSD"}).status == "BLOCKED"
    assert runtime.evaluate_one({"live_execution_enabled": True}).status == "BLOCKED"


def test_runtime_supervisor_explanations_are_bilingual():
    report = RuntimeSupervisorRuntime().explain_one({"historical_data_status": "REVIEW"})
    assert report.recovery_action_en
    assert report.recovery_action_th
    assert report.expected_next_check_en
    assert report.expected_next_check_th


def test_dashboard_renders_runtime_supervisor_without_navigation_regression():
    runtime = DashboardUIRuntime()
    report = runtime.evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    panel = next(panel for panel in report.panels if panel.panel_id == "runtime_supervisor")
    assert panel.status == "READY"
    assert report.navigation_sections == ("Runtime", "Intelligence", "Trading", "Analytics", "AFIP Bank", "Research", "System", "Market", "Order Center")
    html = runtime.render_html({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "Runtime Supervisor" in html
    assert "ระบบกำกับ Runtime" in html
    assert "Live Execution</td><td>False" in html
