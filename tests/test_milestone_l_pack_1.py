from afip.dashboard_ui import DashboardUIRuntime
from afip.paper_execution_foundation import PaperExecutionFoundationRuntime

def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "milestone_k_complete": True, "runtime_certification_status": "CERTIFIED",
        "paper_account_connected": True, "market_data_ready": True,
        "historical_data_ready": True, "risk_limits_configured": True,
        "audit_record_ready": True, "dashboard_explainability_ready": True,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record

def test_paper_execution_foundation_ready():
    r = PaperExecutionFoundationRuntime().evaluate_one(_record())
    assert r.status == "READY"
    assert r.paper_execution_readiness == "PAPER_OBSERVATION_READY"
    assert r.order_status == "NO_ORDER_SENT"

def test_foundation_id_is_deterministic():
    runtime = PaperExecutionFoundationRuntime()
    assert runtime.evaluate_one(_record()).foundation_id == runtime.evaluate_one(_record()).foundation_id

def test_milestone_k_and_runtime_are_required():
    assert "milestone_k_not_complete" in PaperExecutionFoundationRuntime().evaluate_one(_record(milestone_k_complete=False)).block_reasons
    assert "runtime_not_certified" in PaperExecutionFoundationRuntime().evaluate_one(_record(runtime_certification_status="BLOCKED")).block_reasons

def test_data_risk_and_audit_gates():
    runtime = PaperExecutionFoundationRuntime()
    assert "market_data_not_ready" in runtime.evaluate_one(_record(market_data_ready=False)).block_reasons
    assert "risk_limits_not_configured" in runtime.evaluate_one(_record(risk_limits_configured=False)).block_reasons
    assert "audit_record_not_ready" in runtime.evaluate_one(_record(audit_record_ready=False)).block_reasons

def test_version_one_policy_guards():
    runtime = PaperExecutionFoundationRuntime()
    assert "xm_only_policy" in runtime.evaluate_one(_record(broker="OTHER")).block_reasons
    assert "gold_only_policy" in runtime.evaluate_one(_record(symbol="XAUUSD")).block_reasons
    assert "fixed_unit_policy" in runtime.evaluate_one(_record(lot_per_unit=0.02)).block_reasons

def test_execution_guards_and_bilingual_explanations():
    r = PaperExecutionFoundationRuntime().evaluate_one(_record(live_execution_enabled=True))
    assert "live_execution_requested" in r.block_reasons
    assert r.readiness_reason_en and r.readiness_reason_th
    assert r.holding_reason_en and r.holding_reason_th
    assert r.expected_next_action_en and r.expected_next_action_th

def test_dashboard_contains_paper_execution_foundation_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "paper_execution_foundation" in {panel.panel_id for panel in dashboard.panels}
