from afip.dashboard_ui import DashboardUIRuntime
from afip.execution_intelligence_complete import ExecutionIntelligenceCompleteRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "runtime_certification_status": "CERTIFIED", "runtime_integrity_certified": True,
        "dashboard_explainability_ready": True, "audit_record_ready": True,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_milestone_k_completion_gate_passes():
    report = ExecutionIntelligenceCompleteRuntime().evaluate_one(_record())
    assert report.status == "COMPLETE"
    assert report.milestone_k_complete is True
    assert report.completed_pack_count == 9
    assert report.order_status == "NO_ORDER_SENT"


def test_completion_id_is_deterministic():
    runtime = ExecutionIntelligenceCompleteRuntime()
    assert runtime.evaluate_one(_record()).completion_id == runtime.evaluate_one(_record()).completion_id


def test_incomplete_pack_blocks_completion():
    report = ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(pack_statuses={"milestone_k_pack_6": "BLOCKED"}))
    assert report.status == "BLOCKED"
    assert "milestone_k_pack_incomplete" in report.block_reasons


def test_runtime_and_audit_gates_block_completion():
    assert "runtime_execution_not_certified" in ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(runtime_integrity_certified=False)).block_reasons
    assert "audit_chain_not_ready" in ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(audit_record_ready=False)).block_reasons


def test_version_one_policy_guards():
    assert "xm_only_policy" in ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(broker="OTHER")).block_reasons
    assert "gold_only_policy" in ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(symbol="XAUUSD")).block_reasons
    assert "fixed_unit_policy" in ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(lot_per_unit=0.02)).block_reasons


def test_execution_safety_guards_and_bilingual_explanation():
    report = ExecutionIntelligenceCompleteRuntime().evaluate_one(_record(live_execution_enabled=True))
    assert "live_execution_requested" in report.block_reasons
    assert report.completion_reason_en and report.completion_reason_th
    assert report.holding_reason_en and report.holding_reason_th
    assert report.expected_next_action_en and report.expected_next_action_th


def test_dashboard_contains_milestone_k_completion_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "execution_intelligence_complete" in {panel.panel_id for panel in dashboard.panels}
