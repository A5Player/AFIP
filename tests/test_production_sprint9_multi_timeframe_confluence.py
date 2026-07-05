from afip.pipeline.multi_timeframe_confluence_intelligence import MultiTimeframeConfluenceIntelligence
from afip.pipeline.real_market_data_intelligence_wiring import RealMarketDataIntelligenceWiring


class DummyProvider:
    def connection_check(self, symbol="GOLD#"):
        return {"symbol": symbol, "status": "READY"}

    def timeframe_snapshots(self, symbol="GOLD#", count=100):
        return {
            "symbol": symbol,
            "timeframes": {
                "M15": {"source": "MT5_OHLC_M15", "opens": [100, 101], "highs": [102, 104], "lows": [99, 100], "closes": [101, 103], "volumes": [1, 2]},
                "H1": {"source": "MT5_OHLC_H1", "opens": [100, 102], "highs": [103, 106], "lows": [99, 101], "closes": [102, 105], "volumes": [1, 2]},
                "H4": {"source": "MT5_OHLC_H4", "opens": [100, 102], "highs": [104, 107], "lows": [98, 101], "closes": [102, 106], "volumes": [1, 2]},
                "D1": {"source": "MT5_OHLC_D1", "opens": [100, 103], "highs": [105, 108], "lows": [99, 102], "closes": [103, 107], "volumes": [1, 2]},
            },
        }

    def latest_snapshot(self, symbol="GOLD#"):
        return {"source": "MT5_TICK", "closes": [100, 101]}


class DummyPipeline:
    def run(self, snapshot):
        return {
            "mode": "REAL_MARKET_DATA",
            "module_count": 1,
            "intelligence": [{"name": "DummyIntelligence", "direction": "BUY", "confidence": 80, "status": "READY"}],
            "decision": {"action": "BUY", "confidence": 80, "buy_score": 80, "sell_score": 0, "reason": "dummy"},
        }


def test_multi_timeframe_confluence_builds_buy_bias():
    confluence = MultiTimeframeConfluenceIntelligence().build(DummyProvider().timeframe_snapshots()["timeframes"])
    assert confluence["status"] == "READY"
    assert confluence["direction"] == "BUY"
    assert confluence["primary_timeframe"] == "H1"
    assert confluence["aligned_timeframes"] == 4
    assert "H4" in confluence["available_timeframes"]


def test_real_market_data_wiring_exposes_confluence():
    result = RealMarketDataIntelligenceWiring(
        market_data_provider=DummyProvider(),
        intelligence_pipeline=DummyPipeline(),
    ).run(symbol="GOLD#")
    assert result["status"] == "READY"
    assert result["multi_timeframe_confluence"]["direction"] == "BUY"
    assert result["modular_intelligence"]["confluence"]["primary_timeframe"] == "H1"
    assert result["primary_snapshot"]["source"].startswith("MTF_CONFLUENCE_MT5_OHLC")
