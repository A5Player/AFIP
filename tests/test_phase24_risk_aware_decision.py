from afip.pipeline.risk_aware_signal_workflow import RiskAwareSignalWorkflow

def candles(start):
    return [
        {"time":1,"open":start,"high":start+0.8,"low":start-0.3,"close":start+0.4,"tick_volume":100},
        {"time":2,"open":start+0.4,"high":start+1.1,"low":start+0.1,"close":start+0.8,"tick_volume":120},
        {"time":3,"open":start+0.8,"high":start+1.6,"low":start+0.4,"close":start+1.2,"tick_volume":130},
        {"time":4,"open":start+1.2,"high":start+2.0,"low":start+0.9,"close":start+1.7,"tick_volume":150},
        {"time":5,"open":start+1.7,"high":start+2.5,"low":start+1.3,"close":start+2.2,"tick_volume":160},
    ]

def test_risk_aware_workflow_runs():
    data = {"M5": candles(2300), "M15": candles(2301), "H1": candles(2302)}
    result = RiskAwareSignalWorkflow().run("XAUUSD", data, spread=18)
    assert result["mode"] == "SIMULATION"
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")
    assert result["order"]["status"] in ("SIMULATION_ORDER_READY", "NO_ORDER")

def test_risk_blocks_high_spread():
    data = {"M5": candles(2300), "M15": candles(2301), "H1": candles(2302)}
    result = RiskAwareSignalWorkflow().run("XAUUSD", data, spread=80)
    assert result["decision"]["action"] == "WAIT"
    assert "spread_too_high" in result["risk"]["reasons"]
    assert result["order"]["status"] == "NO_ORDER"
