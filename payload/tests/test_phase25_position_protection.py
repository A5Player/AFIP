from afip.position.position_sizer import PositionSizer
from afip.protection.sl_tp_planner import SLTPPlanner
from afip.protection.profit_protection_planner import ProfitProtectionPlanner
from afip.pipeline.protected_signal_workflow import ProtectedSignalWorkflow

def candles(start):
    return [
        {"time":1,"open":start,"high":start+0.8,"low":start-0.3,"close":start+0.4,"tick_volume":100},
        {"time":2,"open":start+0.4,"high":start+1.1,"low":start+0.1,"close":start+0.8,"tick_volume":120},
        {"time":3,"open":start+0.8,"high":start+1.6,"low":start+0.4,"close":start+1.2,"tick_volume":130},
        {"time":4,"open":start+1.2,"high":start+2.0,"low":start+0.9,"close":start+1.7,"tick_volume":150},
        {"time":5,"open":start+1.7,"high":start+2.5,"low":start+1.3,"close":start+2.2,"tick_volume":160},
    ]

def test_position_sizer_returns_safe_lot():
    result = PositionSizer().calculate(balance=1000, risk_usd=30, stop_loss_points=3000)
    assert result["lot"] >= 0.01

def test_sl_tp_planner_buy():
    plan = SLTPPlanner().plan("BUY", 2300.0, stop_loss_points=800, take_profit_points=1200)
    assert plan["status"] == "PLANNED"
    assert plan["sl"] < 2300.0
    assert plan["tp"] > 2300.0

def test_profit_protection_planner():
    plan = ProfitProtectionPlanner().plan(floating_points=1000, confidence=45)
    assert plan["action"] == "PROTECT_AGGRESSIVE"
    assert plan["lock_points"] == 750

def test_protected_signal_workflow_runs():
    data = {"M5": candles(2300), "M15": candles(2301), "H1": candles(2302)}
    result = ProtectedSignalWorkflow().run("XAUUSD", data, spread=18)
    assert result["mode"] == "SIMULATION"
    assert result["protected_order"]["status"] in ("SIMULATION_ORDER_READY", "NO_ORDER")
