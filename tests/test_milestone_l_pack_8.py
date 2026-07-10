from afip.dashboard_ui import DashboardUIRuntime
from afip.demo_execution_certification import DemoExecutionCertificationRuntime


def _observations(count=20, **extra):
    rows = []
    for index in range(count):
        item = {
            "status": "READY",
            "observation_readiness": "SHADOW_OBSERVATION_READY",
            "shadow_observation_id": f"L07-{index:016d}",
            "performance_certification_id": "L06-CERTIFIED",
            "spread_valid": True,
            "latency_valid": True,
            "market_data_fresh": True,
            "market_session_open": True,
            "risk_validation_valid": True,
            "timing_validation_valid": True,
            "market_structure_confirmed": True,
            "independent_trade_plan_valid": True,
            "protected_runner_exposure_included": True,
            "execution_status": "LOCKED_SIMULATION_ONLY",
            "order_status": "NO_ORDER_SENT",
            "broker_request_created": False,
            "order_transmission_attempted": False,
            "block_reasons": (),
            "observed_at_utc": f"2026-07-10T{index:02d}:00:00+00:00",
        }
        item.update(extra)
        rows.append(item)
    return rows


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "performance_certification_id": "L06-CERTIFIED",
        "shadow_observations": _observations(),
        "minimum_observations_required": 20,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT",
        "direct_execution": False,
        "live_execution_enabled": False,
        "traditional_dca_enabled": False,
        "averaging_down_enabled": False,
        "broker_request_created": False,
        "order_transmission_attempted": False,
    }
    record.update(extra)
    return record


def test_demo_execution_certification_is_ready_for_observation_only():
    report = DemoExecutionCertificationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.certified_for_demo_observation is True
    assert report.certified_for_demo_execution is False
    assert report.order_status == "NO_ORDER_SENT"


def test_demo_certification_id_is_deterministic():
    runtime = DemoExecutionCertificationRuntime()
    assert runtime.evaluate_one(_record()).demo_certification_id == runtime.evaluate_one(_record()).demo_certification_id


def test_shadow_sample_and_quality_thresholds_are_enforced():
    runtime = DemoExecutionCertificationRuntime()
    assert "shadow_observation_sample_insufficient" in runtime.evaluate_one(_record(shadow_observations=_observations(5))).block_reasons
    observations = _observations()
    observations[0]["spread_valid"] = False
    observations[1]["spread_valid"] = False
    assert "spread_pass_rate_below_minimum" in runtime.evaluate_one(_record(shadow_observations=observations)).block_reasons


def test_risk_timing_structure_and_market_quality_are_required():
    runtime = DemoExecutionCertificationRuntime()
    for field, reason in (
        ("market_data_fresh", "market_quality_invalid"),
        ("risk_validation_valid", "risk_validation_failed"),
        ("timing_validation_valid", "timing_validation_failed"),
        ("market_structure_confirmed", "market_structure_unconfirmed"),
    ):
        observations = _observations()
        observations[0][field] = False
        assert reason in runtime.evaluate_one(_record(shadow_observations=observations)).block_reasons


def test_evidence_identity_lineage_and_chronology_are_enforced():
    runtime = DemoExecutionCertificationRuntime()
    duplicate = _observations()
    duplicate[1]["shadow_observation_id"] = duplicate[0]["shadow_observation_id"]
    assert "duplicate_or_missing_observation_id" in runtime.evaluate_one(_record(shadow_observations=duplicate)).block_reasons
    wrong_lineage = _observations()
    wrong_lineage[0]["performance_certification_id"] = "OTHER"
    assert "certification_lineage_invalid" in runtime.evaluate_one(_record(shadow_observations=wrong_lineage)).block_reasons
    reversed_rows = list(reversed(_observations()))
    assert "chronological_integrity_invalid" in runtime.evaluate_one(_record(shadow_observations=reversed_rows)).block_reasons


def test_no_dca_and_execution_locks_are_enforced():
    runtime = DemoExecutionCertificationRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons
    assert "order_transmission_attempted" in runtime.evaluate_one(_record(order_transmission_attempted=True)).block_reasons


def test_dashboard_contains_demo_execution_certification_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "demo_execution_certification" in {panel.panel_id for panel in dashboard.panels}
