from afip.pipeline.real_market_data_intelligence_wiring import RealMarketDataIntelligenceWiring


class FakeRealMarketDataProvider:
    def get_multi_timeframe_snapshot(self, symbol):
        candles = {
            "opens": [1, 2, 3, 4, 5],
            "highs": [2, 3, 4, 5, 6],
            "lows": [0.5, 1.5, 2.5, 3.5, 4.5],
            "closes": [1.5, 2.5, 3.5, 4.5, 5.5],
            "spread": 20,
        }
        return {
            "status": "READY",
            "symbol": symbol,
            "requested_symbol": symbol,
            "execution": "LOCKED_SIMULATION_ONLY",
            "timeframes": {
                "M1": dict(candles),
                "M5": dict(candles),
                "M15": dict(candles),
                "H1": dict(candles),
                "H4": dict(candles),
                "D1": dict(candles),
            },
        }

    def get_snapshot(self, symbol, timeframe="H1"):
        return self.get_multi_timeframe_snapshot(symbol)["timeframes"][timeframe]


def test_real_market_data_wiring_runs_modular_intelligence_from_mt5_ohlc_snapshot():
    result = RealMarketDataIntelligenceWiring(
        market_data_provider=FakeRealMarketDataProvider()
    ).run(symbol="GOLD#")

    assert result["status"] in {"READY", "FALLBACK_READY"}
    assert result["symbol"] == "GOLD#"
    assert result["execution"] == "LOCKED_SIMULATION_ONLY"
    assert result["primary_timeframe"] == "H1"
    assert result["modular_intelligence"]["mode"] in {"REAL_MARKET_DATA", "SIMULATION_FALLBACK"}
    assert result["modular_intelligence"]["data_source"] in {"MT5_OHLC_H1", "MTF_CONFLUENCE_MT5_OHLC_H1", "MTF_CONFLUENCE_UNKNOWN"}
