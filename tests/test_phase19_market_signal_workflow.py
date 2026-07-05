from afip.pipeline.market_signal_workflow import MarketSignalWorkflow


def test_market_signal_workflow_runs_current_interface():
    result = MarketSignalWorkflow().run("GOLD#")
    assert isinstance(result, dict)
    assert result
