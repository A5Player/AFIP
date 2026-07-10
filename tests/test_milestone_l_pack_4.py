from afip.dashboard_ui import DashboardUIRuntime
from afip.paper_outcome_evaluation import PaperOutcomeEvaluationRuntime


def _record(**extra):
    record = {
        "broker": "XM", "symbol": "GOLD#", "lot_per_unit": 0.01,
        "paper_decision_status": "READY", "decision_id": "L03-0123456789ABCDEF",
        "outcome_state": "CLOSED", "direction": "BUY", "entry_price": 2400.0,
        "current_price": 2410.0, "exit_price": 2408.0,
        "maximum_favorable_excursion": 12.0, "maximum_adverse_excursion": 3.0,
        "gross_profit": 8.0, "trading_cost": 0.5, "swap_cost": 0.2,
        "planned_risk_amount": 4.0, "data_complete": True, "future_data_used": False,
        "decision_time_utc": "2026-07-10T01:00:00+00:00",
        "outcome_time_utc": "2026-07-10T03:00:00+00:00",
        "independent_position_lifecycle_valid": True,
        "protected_runner_exposure_included": True,
        "traditional_dca_enabled": False, "averaging_down_enabled": False,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
        "direct_execution": False, "live_execution_enabled": False,
    }
    record.update(extra)
    return record


def test_closed_paper_outcome_is_evaluated():
    report = PaperOutcomeEvaluationRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.outcome_classification == "PROFIT"
    assert report.net_profit == 7.3
    assert report.realized_r_multiple == 1.825


def test_outcome_id_is_deterministic():
    runtime = PaperOutcomeEvaluationRuntime()
    assert runtime.evaluate_one(_record()).outcome_id == runtime.evaluate_one(_record()).outcome_id


def test_decision_link_and_data_are_required():
    runtime = PaperOutcomeEvaluationRuntime()
    assert "decision_id_missing" in runtime.evaluate_one(_record(decision_id="")).block_reasons
    assert "outcome_data_incomplete" in runtime.evaluate_one(_record(entry_price=0.0)).block_reasons


def test_future_leakage_and_chronology_are_blocked():
    runtime = PaperOutcomeEvaluationRuntime()
    assert "future_leakage_detected" in runtime.evaluate_one(_record(future_data_used=True)).block_reasons
    assert "chronological_order_invalid" in runtime.evaluate_one(_record(outcome_time_utc="2026-07-09T23:00:00+00:00")).block_reasons


def test_cost_risk_and_quality_are_recorded():
    report = PaperOutcomeEvaluationRuntime().evaluate_one(_record())
    assert report.trading_cost == 0.5
    assert report.swap_cost == 0.2
    assert report.exit_quality in {"EXCELLENT", "GOOD", "EARLY", "RISK_EXIT"}


def test_independent_lifecycle_no_dca_and_execution_locks_are_enforced():
    runtime = PaperOutcomeEvaluationRuntime()
    assert "independent_position_lifecycle_invalid" in runtime.evaluate_one(_record(independent_position_lifecycle_valid=False)).block_reasons
    assert "traditional_dca_enabled" in runtime.evaluate_one(_record(traditional_dca_enabled=True)).block_reasons
    assert "live_execution_requested" in runtime.evaluate_one(_record(live_execution_enabled=True)).block_reasons


def test_dashboard_contains_paper_outcome_evaluation_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "paper_outcome_evaluation" in {panel.panel_id for panel in dashboard.panels}
