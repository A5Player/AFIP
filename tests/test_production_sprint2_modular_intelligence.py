from afip.pipeline.modular_intelligence_pipeline import ModularIntelligencePipeline
from afip.runtime.runtime_v1 import RuntimeV1


def sample_snapshot():
    return {
        "symbol": "XAUUSD",
        "opens": [2300, 2300.4, 2301.0, 2301.5, 2302.0],
        "closes": [2300.4, 2301.0, 2301.5, 2302.0, 2303.2],
        "highs": [2300.8, 2301.3, 2301.9, 2302.4, 2303.6],
        "lows": [2299.8, 2300.2, 2300.7, 2301.0, 2301.8],
        "volumes": [100, 120, 130, 150, 180],
        "spread": 18,
    }


def test_modular_intelligence_pipeline_runs():
    result = ModularIntelligencePipeline().run(sample_snapshot())
    assert result["mode"] == "SIMULATION"
    assert result["module_count"] >= 14
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")


def test_runtime_v1_uses_modular_intelligence():
    result = RuntimeV1().simulate()
    assert result["status"] == "OK"
    assert result["modular_intelligence"]["module_count"] >= 14
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")
