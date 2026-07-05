from afip.pipeline.strategy_signal_workflow import StrategySignalWorkflow

def test_strategy_signal_workflow_buy_or_wait():
    snapshot = {
        "closes": [2300, 2301, 2302, 2303, 2304],
        "highs": [2300.5, 2301.5, 2302.5, 2303.5, 2305],
        "lows": [2299.5, 2300.5, 2301.5, 2302.5, 2303.5],
        "spread": 18,
    }
    result = StrategySignalWorkflow().run(snapshot)
    assert result["mode"] == "SIMULATION"
    assert result["strategy_signal"]["action"] in ("BUY", "SELL", "WAIT")
    assert len(result["strategy_results"]) == 3
