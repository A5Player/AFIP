from afip.dashboard_ui import DashboardUIRuntime
from afip.runtime_execution_certification import RuntimeExecutionCertificationRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "approved_action": "PARTIAL_CLOSE", "supervisor_status": "READY",
        "supervisor_readiness": "READY", "position_state": "OPEN",
        "current_units": 3, "approved_units": 1,
        "simulation_instruction_ready": True,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False,
        "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_certifies_supervised_simulation_instruction():
    report = RuntimeExecutionCertificationRuntime().evaluate_one(_record())
    assert report.status == "CERTIFIED"
    assert report.certification_readiness == "CERTIFIED"
    assert report.runtime_integrity_certified is True
    assert report.audit_record_ready is True
    assert report.order_status == "NO_ORDER_SENT"


def test_certification_id_is_deterministic():
    runtime = RuntimeExecutionCertificationRuntime()
    assert runtime.evaluate_one(_record()).certification_id == runtime.evaluate_one(_record()).certification_id


def test_dependency_failure_blocks_certification():
    report = RuntimeExecutionCertificationRuntime().evaluate_one(_record(dependency_statuses={"smart_exit": "BLOCKED"}))
    assert report.status == "BLOCKED"
    assert "dependencies_not_certified" in report.block_reasons


def test_action_and_position_state_consistency():
    entry = RuntimeExecutionCertificationRuntime().evaluate_one(_record(approved_action="ENTRY", position_state="FLAT", current_units=0, approved_units=2))
    invalid = RuntimeExecutionCertificationRuntime().evaluate_one(_record(approved_action="PARTIAL_CLOSE", approved_units=3))
    assert entry.status == "CERTIFIED"
    assert "position_state_inconsistent" in invalid.block_reasons


def test_policy_and_execution_safety_guards():
    assert "xm_only_policy" in RuntimeExecutionCertificationRuntime().evaluate_one(_record(broker="OTHER")).block_reasons
    assert "fixed_unit_policy" in RuntimeExecutionCertificationRuntime().evaluate_one(_record(lot_per_unit=0.02)).block_reasons
    assert "live_execution_requested" in RuntimeExecutionCertificationRuntime().evaluate_one(_record(live_execution_enabled=True)).block_reasons
    assert "order_status_not_safe" in RuntimeExecutionCertificationRuntime().evaluate_one(_record(order_status="ORDER_SENT")).block_reasons


def test_monitoring_hold_is_certified_and_bilingual():
    report = RuntimeExecutionCertificationRuntime().evaluate_one(_record(approved_action="HOLD", simulation_instruction_ready=False, approved_units=0))
    assert report.status == "CERTIFIED"
    assert report.certification_readiness == "MONITORING_CERTIFIED"
    assert report.certification_reason_en and report.certification_reason_th
    assert report.holding_reason_en and report.holding_reason_th
    assert report.expected_next_action_en and report.expected_next_action_th


def test_dashboard_contains_runtime_execution_certification_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "runtime_execution_certification" in {panel.panel_id for panel in dashboard.panels}
