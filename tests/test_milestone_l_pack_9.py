from afip.dashboard_ui import DashboardUIRuntime
from afip.version1_release_candidate import Version1ReleaseCandidateRuntime


def _record(**extra):
    record = {
        "broker": "XM",
        "symbol": "GOLD#",
        "lot_per_unit": 0.01,
        "paper_execution_foundation_status": "READY",
        "paper_execution_session_monitor_status": "READY",
        "paper_decision_ledger_status": "READY",
        "paper_outcome_evaluation_status": "READY",
        "paper_performance_analytics_status": "READY",
        "paper_performance_certification_status": "READY",
        "shadow_execution_observation_status": "READY",
        "demo_execution_certification_status": "READY",
        "demo_certification_id": "L08-CERTIFIED",
        "certified_for_demo_observation": True,
        "production_health_monitor_ready": True,
        "emergency_safety_system_ready": True,
        "production_report_ready": True,
        "decision_ledger_ready": True,
        "data_quality_certified": True,
        "knowledge_versioning_ready": True,
        "feature_flags_ready": True,
        "operation_manual_en_ready": True,
        "operation_manual_th_ready": True,
        "audit_chain_ready": True,
        "independent_trade_plan_valid": True,
        "protected_runner_exposure_included": True,
        "traditional_dca_enabled": False,
        "averaging_down_enabled": False,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "direct_execution": False,
        "live_execution_enabled": False,
        "order_status": "NO_ORDER_SENT",
        "broker_request_created": False,
        "order_transmission_attempted": False,
    }
    record.update(extra)
    return record


def test_release_candidate_is_ready_but_not_production_certified():
    report = Version1ReleaseCandidateRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.release_candidate_approved is True
    assert report.production_certified is False
    assert report.order_status == "NO_ORDER_SENT"


def test_release_candidate_id_is_deterministic():
    runtime = Version1ReleaseCandidateRuntime()
    assert runtime.evaluate_one(_record()).release_candidate_id == runtime.evaluate_one(_record()).release_candidate_id


def test_all_milestone_l_dependencies_are_required():
    report = Version1ReleaseCandidateRuntime().evaluate_one(
        _record(paper_outcome_evaluation_status="BLOCKED")
    )
    assert "milestone_l_dependency_not_ready" in report.block_reasons
    assert report.all_pack_dependencies_ready is False


def test_operational_controls_and_manuals_are_required():
    runtime = Version1ReleaseCandidateRuntime()
    for field, reason in (
        ("production_health_monitor_ready", "production_health_monitor_not_ready"),
        ("emergency_safety_system_ready", "emergency_safety_system_not_ready"),
        ("data_quality_certified", "data_quality_not_certified"),
        ("operation_manual_th_ready", "operation_manual_th_missing"),
    ):
        assert reason in runtime.evaluate_one(_record(**{field: False})).block_reasons


def test_demo_lineage_and_audit_controls_are_required():
    runtime = Version1ReleaseCandidateRuntime()
    assert "demo_observation_not_certified" in runtime.evaluate_one(
        _record(certified_for_demo_observation=False)
    ).block_reasons
    assert "demo_certification_id_missing" in runtime.evaluate_one(
        _record(demo_certification_id="")
    ).block_reasons
    assert "audit_chain_not_ready" in runtime.evaluate_one(
        _record(audit_chain_ready=False)
    ).block_reasons


def test_permanent_policy_and_execution_locks_are_enforced():
    runtime = Version1ReleaseCandidateRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(
        _record(traditional_dca_enabled=True)
    ).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(
        _record(live_execution_enabled=True)
    ).block_reasons
    assert "order_transmission_attempted" in runtime.evaluate_one(
        _record(order_transmission_attempted=True)
    ).block_reasons


def test_dashboard_contains_production_release_candidate_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "production_release_candidate" in {panel.panel_id for panel in dashboard.panels}
