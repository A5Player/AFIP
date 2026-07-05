from afip.market.candle_normalizer import CandleNormalizer
from afip.market.candle_snapshot_builder import CandleSnapshotBuilder
from afip.market.spread_normalizer import SpreadNormalizer
from afip.pipeline.candle_signal_workflow import CandleSignalWorkflow

def sample_candles():
    return [
        {"time":1,"open":2300.0,"high":2301.0,"low":2299.5,"close":2300.6,"tick_volume":100},
        {"time":2,"open":2300.6,"high":2301.5,"low":2300.0,"close":2301.1,"tick_volume":120},
        {"time":3,"open":2301.1,"high":2302.0,"low":2300.8,"close":2301.8,"tick_volume":140},
        {"time":4,"open":2301.8,"high":2302.8,"low":2301.2,"close":2302.4,"tick_volume":160},
        {"time":5,"open":2302.4,"high":2303.5,"low":2302.0,"close":2303.1,"tick_volume":180},
    ]

def test_candle_normalizer_validates_and_converts():
    candles = CandleNormalizer().normalize_many(sample_candles())
    assert len(candles) == 5
    assert candles[-1].direction() == "BUY"

def test_spread_normalizer_from_bid_ask():
    spread = SpreadNormalizer(point_size=0.01).from_bid_ask(2300.00, 2300.18)
    assert round(spread, 2) == 18.0

def test_candle_snapshot_builder():
    snapshot = CandleSnapshotBuilder().build("XAUUSD", sample_candles(), spread=18)
    assert snapshot["symbol"] == "XAUUSD"
    assert snapshot["candle_count"] == 5
    assert snapshot["closes"][-1] == 2303.1

def test_candle_signal_workflow_runs():
    result = CandleSignalWorkflow().run("XAUUSD", sample_candles(), spread=18)
    assert result["mode"] == "SIMULATION"
    assert result["decision"]["action"] in ("BUY", "SELL", "WAIT")
