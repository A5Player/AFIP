from afip.dashboard_ui import DashboardUIRuntime
from afip.execution_intelligence_foundation import ExecutionIntelligenceFoundationRuntime


def test_safe_actionable_decision_is_ready_for_simulation_only():
    report = ExecutionIntelligenceFoundationRuntime().evaluate_one({
        "portfolio_decision": "ENTER", "portfolio_decision_status": "READY",
        "entry_validation_status": "READY", "approved_units": 1,
    })
    assert report.status == "READY"
    assert report.execution_readiness == "READY_FOR_SIMULATION"
    assert report.simulation_ready is True
    assert report.no_order_sent is True
    assert report.direct_execution is False


def test_waits_without_actionable_entry_and_units():
    report = ExecutionIntelligenceFoundationRuntime().evaluate_one({"portfolio_decision": "WAIT"})
    assert report.status == "WAITING"
    assert report.execution_readiness == "WAITING_FOR_VALIDATION"


def test_live_execution_request_is_blocked():
    report = ExecutionIntelligenceFoundationRuntime().evaluate_one({"live_execution_enabled": True})
    assert report.status == "BLOCKED"
    assert "live_or_direct_execution_requested" in report.block_reasons


def test_non_xm_or_non_gold_is_blocked():
    report = ExecutionIntelligenceFoundationRuntime().evaluate_one({"broker": "EXNESS", "symbol": "EURUSD"})
    assert report.status == "BLOCKED"
    assert "xm_only_policy" in report.block_reasons
    assert "gold_only_policy" in report.block_reasons


def test_fixed_unit_policy_remains_point_zero_one_lot():
    report = ExecutionIntelligenceFoundationRuntime().evaluate_one({"lot_per_unit": 0.02})
    assert report.status == "BLOCKED"
    assert report.lot_per_unit == 0.01
    assert "fixed_unit_policy" in report.block_reasons


def test_dashboard_contains_execution_intelligence_foundation_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "execution_intelligence_foundation" in {panel.panel_id for panel in report.panels}
