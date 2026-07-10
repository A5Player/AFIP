from afip.dashboard_ui import DashboardUIRuntime
from afip.paper_decision_ledger import PaperDecisionLedgerRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "paper_execution_session_status": "READY", "approved_action": "ENTRY",
        "position_state": "FLAT", "direction": "BUY", "requested_units": 1,
        "trade_plan_id": "PLAN-20260710-001", "independent_trade_plan_valid": True,
        "market_context_recorded": True, "news_context_recorded": True,
        "confidence_breakdown_recorded": True, "rejected_alternatives_recorded": True,
        "version_context_recorded": True, "outcome_tracking_ready": True,
        "total_exposure_included": True, "traditional_dca_enabled": False,
        "averaging_down_enabled": False, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_paper_decision_ledger_records_complete_entry():
    report = PaperDecisionLedgerRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.decision_recorded is True
    assert report.order_status == "NO_ORDER_SENT"


def test_decision_id_is_deterministic():
    runtime = PaperDecisionLedgerRuntime()
    assert runtime.evaluate_one(_record()).decision_id == runtime.evaluate_one(_record()).decision_id


def test_action_position_and_units_are_validated():
    runtime = PaperDecisionLedgerRuntime()
    assert "action_position_mismatch" in runtime.evaluate_one(_record(position_state="OPEN")).block_reasons
    assert "requested_units_invalid" in runtime.evaluate_one(_record(requested_units=0)).block_reasons


def test_explainability_and_version_context_are_required():
    runtime = PaperDecisionLedgerRuntime()
    assert "confidence_breakdown_missing" in runtime.evaluate_one(_record(confidence_breakdown_recorded=False)).block_reasons
    assert "rejected_alternatives_missing" in runtime.evaluate_one(_record(rejected_alternatives_recorded=False)).block_reasons
    assert "version_context_missing" in runtime.evaluate_one(_record(version_context_recorded=False)).block_reasons


def test_protected_runner_is_independent_but_included_in_exposure():
    report = PaperDecisionLedgerRuntime().evaluate_one(_record(approved_action="HOLD", position_state="OPEN", requested_units=0, protected_runner=True, profit_locked=True))
    assert report.protected_runner_excluded_from_new_entry_count is True
    assert report.total_exposure_included is True


def test_no_dca_and_execution_locks_are_enforced():
    runtime = PaperDecisionLedgerRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "averaging_down_enabled" in runtime.evaluate_one(_record(averaging_down_enabled=True)).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons


def test_dashboard_contains_paper_decision_ledger_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "paper_decision_ledger" in {panel.panel_id for panel in dashboard.panels}
