from afip.pipeline.market_signal_workflow import MarketSignalWorkflow

def test_market_signal_workflow_returns_decision():
    result = MarketSignalWorkflow().run("XAUUSD")
    assert result["mode"] == "SIMULATION"
    assert result["snapshot"]["symbol"] == "XAUUSD"
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")

def test_market_signal_workflow_stress_penalty():
    result = MarketSignalWorkflow().run("XAUUSD", stress=True)
    assert result["snapshot"]["source"] == "SIMULATION_STRESS"
    assert result["score"]["penalties"] >= 35
