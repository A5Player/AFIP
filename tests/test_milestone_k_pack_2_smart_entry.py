from afip.dashboard_ui import DashboardUIRuntime
from afip.smart_entry import SmartEntryRuntime


def _ready(**extra):
    record = {
        "execution_readiness": "READY_FOR_SIMULATION",
        "portfolio_decision": "ENTER",
        "direction": "BUY",
        "approved_units": 1,
        "reference_price": 2400.0,
        "stop_loss_price": 2390.0,
        "take_profit_price": 2420.0,
    }
    record.update(extra)
    return record


def test_ready_buy_plan_is_simulation_only():
    report = SmartEntryRuntime().evaluate_one(_ready())
    assert report.status == "READY"
    assert report.simulation_instruction_ready is True
    assert report.no_order_sent is True
    assert report.total_lot == 0.01


def test_invalid_buy_price_structure_is_blocked():
    report = SmartEntryRuntime().evaluate_one(_ready(stop_loss_price=2410.0))
    assert report.status == "BLOCKED"
    assert "buy_price_structure_invalid" in report.block_reasons


def test_low_reward_risk_is_blocked():
    report = SmartEntryRuntime().evaluate_one(_ready(take_profit_price=2405.0))
    assert "reward_risk_below_minimum" in report.block_reasons


def test_fixed_unit_policy_is_enforced():
    report = SmartEntryRuntime().evaluate_one(_ready(lot_per_unit=0.02))
    assert "fixed_unit_policy" in report.block_reasons
    assert report.lot_per_unit == 0.01


def test_live_execution_request_is_blocked():
    report = SmartEntryRuntime().evaluate_one(_ready(live_execution_enabled=True))
    assert "live_or_direct_execution_requested" in report.block_reasons


def test_dashboard_contains_smart_entry_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "smart_entry" in {panel.panel_id for panel in report.panels}
