from afip.pipeline.simulation_signal_pipeline import SimulationSignalPipeline


def test_simulation_pipeline_buy_candidate():
    snapshot = {
        "closes": [2300.0, 2300.5, 2301.0, 2302.0, 2303.0],
        "highs": [2300.5, 2301.0, 2301.5, 2302.5, 2303.5],
        "lows": [2299.5, 2300.0, 2300.5, 2301.5, 2302.5],
        "spread": 18,
    }
    result = SimulationSignalPipeline().run(snapshot)
    assert result["mode"] == "SIMULATION"
    assert result["decision"]["action"] in ("BUY", "WAIT")
    assert "overall_confidence" in result["score"]


def test_simulation_pipeline_blocks_bad_liquidity():
    snapshot = {
        "closes": [2300.0, 2300.5, 2301.0, 2302.0, 2303.0],
        "highs": [2300.5, 2301.0, 2301.5, 2302.5, 2303.5],
        "lows": [2299.5, 2300.0, 2300.5, 2301.5, 2302.5],
        "spread": 80,
    }
    result = SimulationSignalPipeline().run(snapshot)
    assert result["score"]["penalties"] >= 35
