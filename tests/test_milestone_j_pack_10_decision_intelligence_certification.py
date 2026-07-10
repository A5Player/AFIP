from afip.dashboard_ui import DashboardUIRuntime
from afip.decision_intelligence_certification import DecisionIntelligenceCertificationRuntime


def test_certification_passes_with_default_safe_controls():
    report = DecisionIntelligenceCertificationRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#"})
    assert report.status == "CERTIFIED"
    assert report.certification_level == "DECISION_INTELLIGENCE_COMPLETE"
    assert report.decision_intelligence_ready is True
    assert report.direct_execution is False


def test_live_execution_request_blocks_certification():
    report = DecisionIntelligenceCertificationRuntime().evaluate_one({"live_execution_enabled": True})
    assert report.status == "BLOCKED"
    assert "execution_policy" in report.failed_checks


def test_non_gold_or_non_xm_blocks_certification():
    report = DecisionIntelligenceCertificationRuntime().evaluate_one({"broker": "EXNESS", "symbol": "EURUSD"})
    assert report.status == "BLOCKED"
    assert "version1_market_policy" in report.failed_checks


def test_fixed_unit_policy_is_certified_only_at_point_zero_one_lot():
    report = DecisionIntelligenceCertificationRuntime().evaluate_one({"lot_per_unit": 0.02})
    assert report.status == "BLOCKED"
    assert "fixed_unit_policy" in report.failed_checks


def test_failed_component_blocks_certification():
    report = DecisionIntelligenceCertificationRuntime().evaluate_one({"entry_validation_status": "BLOCKED"})
    assert report.status == "BLOCKED"
    assert "entry_validation" in report.failed_checks


def test_dashboard_contains_decision_intelligence_certification_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    panel_ids = {panel.panel_id for panel in report.panels}
    assert "decision_intelligence_certification" in panel_ids
