from afip.runtime.runtime_v1 import RuntimeV1


def test_runtime_v1_real_simulate_returns_decision_and_report():
    result = RuntimeV1().simulate()
    assert result["status"] == "OK"
    assert result["mode"] == "SIMULATION"
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")
    assert result["order"]["status"] in ("SIMULATION_ORDER_READY", "NO_ORDER")
    assert result["report"]["status"] == "REPORT_READY"
