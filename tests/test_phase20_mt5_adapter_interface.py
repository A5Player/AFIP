from afip.broker.mt5_adapter import MT5Adapter
from afip.market.mt5_market_data_provider import MT5MarketDataProvider
from afip.pipeline.market_signal_workflow import MarketSignalWorkflow


def test_mt5_adapter_disabled_is_safe():
    adapter = MT5Adapter(enabled=False)
    tick = adapter.latest_tick("XAUUSD")
    assert tick["available"] is False
    assert tick["reason"] == "mt5_adapter_disabled"


def test_mt5_provider_falls_back_to_simulation():
    provider = MT5MarketDataProvider(adapter=MT5Adapter(enabled=False))
    snapshot = provider.latest_snapshot("XAUUSD")
    assert snapshot["source"] == "SIMULATION_FALLBACK"
    assert snapshot["fallback_reason"] == "mt5_adapter_disabled"


def test_market_signal_workflow_runs_with_safe_default():
    result = MarketSignalWorkflow().run("XAUUSD")
    assert result["mode"] == "SIMULATION"
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")
