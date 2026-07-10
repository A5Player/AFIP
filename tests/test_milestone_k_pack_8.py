from afip.dashboard_ui import DashboardUIRuntime
from afip.execution_supervisor import ExecutionSupervisorRuntime


def _open(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "position_side": "BUY",
        "position_state": "OPEN", "current_units": 3, "lot_per_unit": 0.01,
        "risk_allowed": True, "timing_allowed": True, "trading_cost_valid": True,
        "market_structure_confirmed": True, "market_regime_confirmed": True,
        "dependency_reports_valid": True,
    }
    record.update(extra)
    return record


def test_supervisor_selects_single_highest_priority_action():
    report = ExecutionSupervisorRuntime().evaluate_one(_open(requested_actions=["TRAIL_STOP", "PARTIAL_CLOSE"], approved_close_units=1))
    assert report.status == "READY"
    assert report.approved_action == "PARTIAL_CLOSE"
    assert report.rejected_actions == ("TRAIL_STOP",)
    assert report.conflict_detected is True
    assert report.simulation_instruction_ready is True
    assert report.order_status == "NO_ORDER_SENT"


def test_exit_has_priority_over_position_adjustments():
    report = ExecutionSupervisorRuntime().evaluate_one(_open(requested_actions=["MOVE_STOP_LOSS", "CHANGE_TAKE_PROFIT", "EXIT"]))
    assert report.approved_action == "EXIT"
    assert report.approved_units == 3


def test_entry_requires_flat_position_and_fixed_units():
    blocked = ExecutionSupervisorRuntime().evaluate_one(_open(requested_actions=["ENTRY"], entry_units=1))
    ready = ExecutionSupervisorRuntime().evaluate_one(_open(position_state="FLAT", current_units=0, requested_actions=["ENTRY"], entry_units=2))
    assert "entry_requires_flat_position" in blocked.block_reasons
    assert ready.status == "READY"
    assert ready.approved_units == 2


def test_partial_close_requires_valid_remaining_position():
    report = ExecutionSupervisorRuntime().evaluate_one(_open(requested_actions=["PARTIAL_CLOSE"], approved_close_units=3))
    assert "partial_close_units_invalid" in report.block_reasons


def test_policy_risk_timing_dependencies_and_live_guards():
    assert "xm_only_policy" in ExecutionSupervisorRuntime().evaluate_one(_open(broker="OTHER")).block_reasons
    assert "risk_not_approved" in ExecutionSupervisorRuntime().evaluate_one(_open(risk_allowed=False)).block_reasons
    assert "timing_not_approved" in ExecutionSupervisorRuntime().evaluate_one(_open(timing_allowed=False)).block_reasons
    assert "dependency_reports_invalid" in ExecutionSupervisorRuntime().evaluate_one(_open(dependency_reports_valid=False)).block_reasons
    assert "live_or_direct_execution_requested" in ExecutionSupervisorRuntime().evaluate_one(_open(live_execution_enabled=True)).block_reasons


def test_hold_and_bilingual_explainability():
    report = ExecutionSupervisorRuntime().evaluate_one(_open())
    assert report.supervisor_readiness == "MONITORING"
    assert report.approved_action == "HOLD"
    assert report.supervision_reason_en and report.supervision_reason_th
    assert report.holding_reason_en and report.holding_reason_th
    assert report.expected_next_action_en and report.expected_next_action_th
    assert report.no_order_sent is True


def test_dashboard_contains_execution_supervisor_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "execution_supervisor" in {panel.panel_id for panel in dashboard.panels}
