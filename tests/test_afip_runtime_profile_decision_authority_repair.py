from types import SimpleNamespace

from afip.broker.mt5_adapter import MT5Adapter
from afip.demo_execution_gateway.runtime import DemoExecutionGateway
from afip.runtime.runtime_v1 import RuntimeV1


class _MT5:
    def __init__(self):
        self.initialize_calls = 0

    def initialize(self):
        self.initialize_calls += 1
        return True


def test_prebound_adapter_does_not_reinitialize_mt5_session():
    mt5 = _MT5()
    adapter = MT5Adapter(mt5_client=mt5, enabled=True)
    adapter.initialized = True

    result = adapter.initialize()

    assert result == {"available": True, "initialized": True, "reason": "already_initialized"}
    assert mt5.initialize_calls == 0


def test_gateway_production_simulation_reuses_profile_mt5_and_real_balance(monkeypatch):
    mt5 = _MT5()
    captured = {}

    def fake_simulate(self, **kwargs):
        captured.update(kwargs)
        return {"decision": {"action": "WAIT", "confidence": 0.0}}

    monkeypatch.setattr(RuntimeV1, "simulate", fake_simulate)

    DemoExecutionGateway._production_simulate(mt5, SimpleNamespace(balance=4321.25))

    provider = captured["market_data_provider"]
    assert provider.adapter.mt5_client is mt5
    assert provider.adapter.initialized is True
    assert captured["balance"] == 4321.25
    assert captured["allow_fallback"] is False


def test_intelligence_snapshot_records_module_votes_and_pipeline_stage():
    result = {
        "data_status": "READY",
        "data_source": "MT5_OHLC_H1",
        "symbol": "GOLD#",
        "primary_timeframe": "H1",
        "modular_intelligence": {
            "intelligence": [
                {
                    "name": "MarketStructureIntelligence",
                    "status": "READY",
                    "direction": "SELL",
                    "confidence": 82.0,
                    "reason": "bearish_structure",
                    "private_debug": "must_not_leak",
                }
            ]
        },
        "decision": {"action": "SELL", "confidence": 82.0, "reason": "decision_intelligence_sell_edge"},
    }

    snapshot = DemoExecutionGateway._intelligence_snapshot(result)
    pipeline = DemoExecutionGateway._decision_pipeline(snapshot)

    assert snapshot["intelligence_votes"] == (
        {
            "name": "MarketStructureIntelligence",
            "status": "READY",
            "direction": "SELL",
            "confidence": 82.0,
            "reason": "bearish_structure",
        },
    )
    assert "MODULAR_INTELLIGENCE" in pipeline
