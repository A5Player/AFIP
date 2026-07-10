from afip.dashboard_ui import DashboardUIRuntime
from afip.dynamic_take_profit import DynamicTakeProfitRuntime

def _base(**extra):
    record={"position_side":"BUY","current_units":2,"reference_price":2400.0,"current_stop_loss":2380.0,"current_take_profit":2440.0,"proposed_take_profit":2460.0,"take_profit_action":"CHANGE_TAKE_PROFIT","minimum_reward_risk":1.0}
    record.update(extra); return record

def test_buy_take_profit_change_is_simulation_only():
    r=DynamicTakeProfitRuntime().evaluate_one(_base()); assert r.status=="READY" and r.change_approved and r.reward_risk_after==3.0 and r.no_order_sent

def test_buy_take_profit_must_remain_above_market():
    assert "buy_take_profit_invalid" in DynamicTakeProfitRuntime().evaluate_one(_base(proposed_take_profit=2390.0)).block_reasons

def test_sell_take_profit_must_remain_below_market():
    r=DynamicTakeProfitRuntime().evaluate_one(_base(position_side="SELL",current_stop_loss=2420.0,current_take_profit=2360.0,proposed_take_profit=2340.0)); assert r.status=="READY" and r.change_approved

def test_reward_risk_minimum_is_enforced():
    assert "reward_risk_below_minimum" in DynamicTakeProfitRuntime().evaluate_one(_base(proposed_take_profit=2410.0)).block_reasons

def test_live_request_is_blocked():
    assert "live_or_direct_execution_requested" in DynamicTakeProfitRuntime().evaluate_one(_base(live_execution_enabled=True)).block_reasons

def test_dashboard_contains_dynamic_take_profit_panel():
    r=DashboardUIRuntime().evaluate_one({"broker":"XM","symbol":"GOLD#","mode":"PAPER"}); assert "dynamic_take_profit" in {p.panel_id for p in r.panels}
