from afip.dashboard_ui import DashboardUIRuntime
from afip.paper_performance_certification import PaperPerformanceCertificationRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "analytics_status": "READY", "analytics_id": "L05-ABC",
        "eligible_outcomes": 40, "minimum_sample_required": 30, "sample_sufficient": True,
        "expectancy_r": 0.25, "minimum_expectancy_r": 0.05,
        "profit_factor": 1.6, "minimum_profit_factor": 1.1,
        "maximum_drawdown": 20.0, "maximum_allowed_drawdown": 100.0,
        "cost_to_gross_profit_percent": 10.0, "maximum_cost_ratio_percent": 35.0,
        "net_profit": 100.0, "data_integrity_valid": True,
        "future_leakage_blocked": True, "incomplete_data_blocked": True,
        "independent_position_lifecycle_valid": True,
        "protected_runner_exposure_included": True,
        "traditional_dca_enabled": False, "averaging_down_enabled": False,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_paper_performance_certification_is_ready():
    report = PaperPerformanceCertificationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.certified_for_shadow_observation is True
    assert report.certified_for_demo_execution is False


def test_certification_id_is_deterministic():
    runtime = PaperPerformanceCertificationRuntime()
    assert runtime.evaluate_one(_record()).certification_id == runtime.evaluate_one(_record()).certification_id


def test_statistical_thresholds_are_enforced():
    runtime = PaperPerformanceCertificationRuntime()
    assert "sample_insufficient" in runtime.evaluate_one(_record(eligible_outcomes=5, sample_sufficient=False)).block_reasons
    assert "expectancy_below_minimum" in runtime.evaluate_one(_record(expectancy_r=-0.1)).block_reasons
    assert "profit_factor_below_minimum" in runtime.evaluate_one(_record(profit_factor=0.9)).block_reasons


def test_drawdown_cost_and_profit_gates_are_enforced():
    runtime = PaperPerformanceCertificationRuntime()
    assert "drawdown_above_limit" in runtime.evaluate_one(_record(maximum_drawdown=101.0)).block_reasons
    assert "cost_ratio_above_limit" in runtime.evaluate_one(_record(cost_to_gross_profit_percent=40.0)).block_reasons
    assert "net_profit_not_positive" in runtime.evaluate_one(_record(net_profit=0.0)).block_reasons


def test_data_integrity_and_pack5_link_are_required():
    runtime = PaperPerformanceCertificationRuntime()
    assert "analytics_not_ready" in runtime.evaluate_one(_record(analytics_status="BLOCKED")).block_reasons
    assert "analytics_id_missing" in runtime.evaluate_one(_record(analytics_id="")).block_reasons
    assert "data_integrity_invalid" in runtime.evaluate_one(_record(future_leakage_blocked=False)).block_reasons


def test_no_dca_exposure_and_execution_locks_are_enforced():
    runtime = PaperPerformanceCertificationRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "protected_runner_exposure_excluded" in runtime.evaluate_one(_record(protected_runner_exposure_included=False)).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons


def test_dashboard_contains_paper_performance_certification_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "paper_performance_certification" in {panel.panel_id for panel in dashboard.panels}
