from afip.pipeline.multi_timeframe_signal_workflow import MultiTimeframeSignalWorkflow

def candles(start):
    return [
        {"time":1,"open":start,"high":start+0.8,"low":start-0.3,"close":start+0.4,"tick_volume":100},
        {"time":2,"open":start+0.4,"high":start+1.1,"low":start+0.1,"close":start+0.8,"tick_volume":120},
        {"time":3,"open":start+0.8,"high":start+1.6,"low":start+0.4,"close":start+1.2,"tick_volume":130},
        {"time":4,"open":start+1.2,"high":start+2.0,"low":start+0.9,"close":start+1.7,"tick_volume":150},
        {"time":5,"open":start+1.7,"high":start+2.5,"low":start+1.3,"close":start+2.2,"tick_volume":160},
    ]

def test_multi_timeframe_workflow_runs():
    data = {"M5": candles(2300), "M15": candles(2301), "H1": candles(2302)}
    result = MultiTimeframeSignalWorkflow().run("XAUUSD", data, spread=18)
    assert result["mode"] == "SIMULATION"
    assert result["trend_consensus"]["direction"] in ("BUY", "SELL", "FLAT")
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")

def test_multi_timeframe_contains_regime():
    data = {"M5": candles(2300), "H1": candles(2302)}
    result = MultiTimeframeSignalWorkflow().run("XAUUSD", data, spread=18)
    assert result["market_regime"]["regime"] in ("QUIET", "NORMAL", "EXPANSION", "UNKNOWN")
