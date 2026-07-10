from afip.dashboard_ui import DashboardUIRuntime
from afip.paper_performance_analytics import PaperPerformanceAnalyticsRuntime


def _outcome(outcome_id="L04-A", net_profit=10.0, realized_r_multiple=1.0, **extra):
    item = {
        "outcome_id": outcome_id, "status": "READY", "outcome_state": "CLOSED",
        "decision_link_valid": True, "data_complete": True, "future_data_used": False,
        "future_leakage_blocked": True, "net_profit": net_profit,
        "realized_r_multiple": realized_r_multiple, "trading_cost": 0.5, "swap_cost": 0.2,
    }
    item.update(extra)
    return item


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "outcomes": [_outcome(), _outcome("L04-B", -5.0, -0.5)],
        "minimum_sample_required": 2, "independent_position_lifecycle_valid": True,
        "protected_runner_exposure_included": True, "traditional_dca_enabled": False,
        "averaging_down_enabled": False, "execution_status": "LOCKED_SIMULATION_ONLY",
        "order_status": "NO_ORDER_SENT", "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_paper_performance_analytics_is_ready():
    report = PaperPerformanceAnalyticsRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.eligible_outcomes == 2
    assert report.sample_sufficient is True


def test_analytics_id_is_deterministic():
    runtime = PaperPerformanceAnalyticsRuntime()
    assert runtime.evaluate_one(_record()).analytics_id == runtime.evaluate_one(_record()).analytics_id


def test_performance_metrics_are_calculated():
    report = PaperPerformanceAnalyticsRuntime().evaluate_one(_record())
    assert report.win_rate_percent == 50.0
    assert report.net_profit == 5.0
    assert report.profit_factor == 2.0
    assert report.maximum_drawdown == 5.0


def test_ineligible_outcomes_are_rejected():
    report = PaperPerformanceAnalyticsRuntime().evaluate_one(_record(outcomes=[_outcome(future_data_used=True), _outcome("L04-B")]))
    assert report.eligible_outcomes == 1
    assert report.rejected_outcomes == 1


def test_empty_or_invalid_inputs_are_blocked():
    runtime = PaperPerformanceAnalyticsRuntime()
    assert "paper_outcomes_missing" in runtime.evaluate_one(_record(outcomes=[])).block_reasons
    assert "eligible_outcomes_missing" in runtime.evaluate_one(_record(outcomes=[_outcome(status="BLOCKED")])).block_reasons


def test_no_dca_exposure_and_execution_locks_are_enforced():
    runtime = PaperPerformanceAnalyticsRuntime()
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "protected_runner_exposure_excluded" in runtime.evaluate_one(_record(protected_runner_exposure_included=False)).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons


def test_dashboard_contains_paper_performance_analytics_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "paper_performance_analytics" in {panel.panel_id for panel in dashboard.panels}
