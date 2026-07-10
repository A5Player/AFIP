from afip.dashboard_ui import DashboardUIRuntime
from afip.production_readiness_complete import ProductionReadinessCompleteRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "release_candidate_ready": True, "release_candidate_id": "L09-READY",
        "all_milestone_l_packs_ready": True,
        "production_health_monitor_ready": True, "emergency_safety_system_ready": True,
        "production_report_ready": True, "decision_ledger_ready": True,
        "data_quality_certified": True, "knowledge_versioning_ready": True,
        "feature_flags_ready": True, "operation_manual_en_ready": True,
        "operation_manual_th_ready": True, "audit_chain_ready": True,
        "independent_trade_plan_valid": True, "protected_runner_exposure_included": True,
        "traditional_dca_enabled": False, "averaging_down_enabled": False,
        "execution_status": "LOCKED_SIMULATION_ONLY", "direct_execution": False,
        "live_execution_enabled": False, "order_status": "NO_ORDER_SENT",
        "broker_request_created": False, "order_transmission_attempted": False,
    }
    record.update(extra); return record


def test_milestone_l_completes_without_production_certification():
    report = ProductionReadinessCompleteRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.milestone_l_complete is True
    assert report.ready_for_milestone_m is True
    assert report.production_certified is False
    assert report.order_status == "NO_ORDER_SENT"


def test_completion_id_is_deterministic():
    runtime = ProductionReadinessCompleteRuntime()
    assert runtime.evaluate_one(_record()).completion_id == runtime.evaluate_one(_record()).completion_id


def test_release_candidate_lineage_is_required():
    runtime = ProductionReadinessCompleteRuntime()
    assert "release_candidate_not_ready" in runtime.evaluate_one(_record(release_candidate_ready=False)).block_reasons
    assert "release_candidate_id_missing" in runtime.evaluate_one(_record(release_candidate_id="")).block_reasons


def test_all_milestone_l_packs_and_controls_are_required():
    runtime = ProductionReadinessCompleteRuntime()
    assert "milestone_l_packs_incomplete" in runtime.evaluate_one(_record(all_milestone_l_packs_ready=False)).block_reasons
    assert "emergency_safety_system_not_ready" in runtime.evaluate_one(_record(emergency_safety_system_ready=False)).block_reasons
    assert "data_quality_not_certified" in runtime.evaluate_one(_record(data_quality_certified=False)).block_reasons


def test_manual_audit_and_knowledge_controls_are_required():
    runtime = ProductionReadinessCompleteRuntime()
    assert "operation_manual_th_missing" in runtime.evaluate_one(_record(operation_manual_th_ready=False)).block_reasons
    assert "audit_chain_not_ready" in runtime.evaluate_one(_record(audit_chain_ready=False)).block_reasons
    assert "knowledge_versioning_not_ready" in runtime.evaluate_one(_record(knowledge_versioning_ready=False)).block_reasons


def test_permanent_policy_and_execution_locks_are_enforced():
    runtime = ProductionReadinessCompleteRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons
    assert "order_transmission_attempted" in runtime.evaluate_one(_record(order_transmission_attempted=True)).block_reasons


def test_dashboard_contains_production_readiness_complete_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "production_readiness_complete" in {panel.panel_id for panel in dashboard.panels}
