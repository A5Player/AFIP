from afip.dashboard_ui import DashboardUIRuntime
from afip.smart_exit import SmartExitRuntime

def _base(**extra):
    record = {"portfolio_decision":"HOLD","current_units":2,"reference_price":2400.0,"stop_loss_price":2390.0,"take_profit_price":2420.0}
    record.update(extra)
    return record

def test_hold_plan_is_simulation_only():
    r=SmartExitRuntime().evaluate_one(_base())
    assert r.status=="READY" and r.action=="HOLD" and r.no_order_sent is True

def test_partial_close_requires_multiple_units():
    r=SmartExitRuntime().evaluate_one(_base(portfolio_decision="PARTIAL_CLOSE",current_units=1,close_units=1))
    assert "partial_close_requires_multiple_units" in r.block_reasons

def test_partial_close_keeps_remaining_units():
    r=SmartExitRuntime().evaluate_one(_base(portfolio_decision="PARTIAL_CLOSE",current_units=3,close_units=1))
    assert r.status=="READY" and r.remaining_units==2

def test_full_exit_requires_all_units():
    r=SmartExitRuntime().evaluate_one(_base(portfolio_decision="EXIT",current_units=3,close_units=2))
    assert "full_exit_units_invalid" in r.block_reasons

def test_live_request_is_blocked():
    r=SmartExitRuntime().evaluate_one(_base(live_execution_enabled=True))
    assert "live_or_direct_execution_requested" in r.block_reasons

def test_dashboard_contains_smart_exit_panel():
    report=DashboardUIRuntime().evaluate_one({"broker":"XM","symbol":"GOLD#","mode":"PAPER"})
    assert "smart_exit" in {p.panel_id for p in report.panels}
