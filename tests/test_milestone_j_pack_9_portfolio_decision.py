from datetime import datetime, timezone

from afip.portfolio_decision import PortfolioDecisionRuntime
from afip.dashboard_ui import DashboardUIRuntime


def _now():
    return datetime(2026, 7, 10, 4, 0, tzinfo=timezone.utc)


def test_entry_is_capped_by_available_portfolio_units():
    report = PortfolioDecisionRuntime().evaluate_one({
        "current_time_utc": _now(), "symbol": "GOLD#", "current_units": 1, "maximum_units": 3,
        "entry_validation": {"entry_approved": True, "approved_units": 3, "selected_direction": "BUY"},
    })
    assert report.portfolio_decision == "HOLD"
    assert report.approved_units == 1
    assert report.direct_execution is False


def test_entry_is_approved_when_portfolio_is_flat_and_capacity_exists():
    report = PortfolioDecisionRuntime().evaluate_one({
        "current_time_utc": _now(), "symbol": "GOLD#", "current_units": 0, "maximum_units": 3,
        "entry_validation": {"entry_approved": True, "approved_units": 2, "selected_direction": "BUY"},
    })
    assert report.status == "READY"
    assert report.portfolio_decision == "ENTER"
    assert report.approved_units == 2


def test_exit_has_priority_for_open_position():
    report = PortfolioDecisionRuntime().evaluate_one({
        "current_time_utc": _now(), "symbol": "GOLD#", "current_units": 2, "maximum_units": 3,
        "exit_validation": {"approved_action": "EXIT", "approved_units": 2, "action_approved": True},
        "entry_validation": {"entry_approved": True, "approved_units": 1, "selected_direction": "BUY"},
    })
    assert report.portfolio_decision == "EXIT"
    assert report.approved_units == 2


def test_risk_block_forces_wait_when_flat():
    report = PortfolioDecisionRuntime().evaluate_one({
        "current_time_utc": _now(), "symbol": "GOLD#", "current_units": 0, "maximum_units": 3,
        "risk_allowed": False,
        "entry_validation": {"entry_approved": True, "approved_units": 1, "selected_direction": "SELL"},
    })
    assert report.status == "WAITING"
    assert report.portfolio_decision == "WAIT"
    assert "portfolio_risk_policy_blocks_decision" in report.decisions[0].block_reasons


def test_non_gold_symbol_is_blocked():
    report = PortfolioDecisionRuntime().evaluate_one({
        "current_time_utc": _now(), "symbol": "EURUSD", "current_units": 0, "maximum_units": 1,
        "entry_validation": {"entry_approved": True, "approved_units": 1, "selected_direction": "BUY"},
    })
    assert report.portfolio_decision == "WAIT"
    assert "version1_gold_only_required" in report.decisions[0].block_reasons


def test_dashboard_contains_portfolio_decision_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    panel_ids = {panel.panel_id for panel in report.panels}
    assert "portfolio_decision" in panel_ids
