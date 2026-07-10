from afip.dashboard_ui import DashboardUIRuntime
from afip.production_certification import ProductionCertificationRuntime


def test_production_certification_passes_complete_bringup():
    report = ProductionCertificationRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#"})
    assert report.status == "CERTIFIED"
    assert report.certification_level == "PRODUCTION_BRINGUP_COMPLETE"
    assert report.passed_checks == report.total_checks == 10
    assert report.market_intelligence_ready is True


def test_production_certification_blocks_failed_dependency():
    report = ProductionCertificationRuntime().evaluate_one({"runtime_supervisor_status": "FAILED"})
    assert report.status == "BLOCKED"
    assert "runtime_supervisor" in report.failed_checks
    assert report.market_intelligence_ready is False


def test_production_certification_blocks_version1_and_live_policy():
    runtime = ProductionCertificationRuntime()
    assert runtime.evaluate_one({"broker": "EXNESS"}).status == "BLOCKED"
    assert runtime.evaluate_one({"symbol": "EURUSD"}).status == "BLOCKED"
    assert runtime.evaluate_one({"live_execution_enabled": True}).status == "BLOCKED"


def test_production_certification_keeps_execution_locked():
    report = ProductionCertificationRuntime().evaluate_one({})
    assert report.live_execution_enabled is False
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.trading_logic_changed is False


def test_production_certification_explanations_are_bilingual():
    report = ProductionCertificationRuntime().explain_one({})
    assert report.certification_summary_en
    assert report.certification_summary_th
    assert report.next_action_en
    assert report.next_action_th


def test_dashboard_renders_certification_without_navigation_regression():
    runtime = DashboardUIRuntime()
    report = runtime.evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    panel = next(panel for panel in report.panels if panel.panel_id == "production_certification")
    assert panel.status == "CERTIFIED"
    assert report.navigation_sections == ("Runtime", "Intelligence", "Trading", "Analytics", "AFIP Bank", "Research", "System", "Market", "Order Center")
    html = runtime.render_html({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "Production Certification" in html
    assert "การรับรอง Production" in html
    assert "Market Intelligence Ready</td><td>True" in html
