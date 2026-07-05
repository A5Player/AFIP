from afip.pipeline.real_market_data_intelligence_wiring import RealMarketDataIntelligenceWiring
from afip.runtime.runtime_v1 import RuntimeV1


class FakeRealMarketDataProvider:
    def connection_check(self, symbol="GOLD#"):
        return {
            "status": "READY",
            "symbol": "GOLD#",
            "requested_symbol": symbol,
            "execution": "LOCKED_SIMULATION_ONLY",
        }

    def timeframe_snapshots(self, symbol="GOLD#", timeframes=None, count=100):
        snapshot = {
            "symbol": symbol,
            "opens": [2300.0, 2301.0, 2302.0, 2303.0, 2304.0],
            "highs": [2301.0, 2302.0, 2303.0, 2304.0, 2305.0],
            "lows": [2299.0, 2300.0, 2301.0, 2302.0, 2303.0],
            "closes": [2300.5, 2301.5, 2302.5, 2303.5, 2304.5],
            "volumes": [100, 120, 130, 140, 160],
            "spread": 18,
            "source": "MT5_OHLC_H1",
            "candle_count": 5,
        }
        return {
            "symbol": symbol,
            "source": "MT5_OHLC",
            "timeframes": {"H1": snapshot},
            "fallback_reasons": {},
            "execution": "LOCKED_SIMULATION_ONLY",
        }

    def latest_snapshot(self, symbol="GOLD#"):
        return self.timeframe_snapshots(symbol)["timeframes"]["H1"]


def test_real_market_data_wiring_runs_modular_intelligence_from_mt5_ohlc_snapshot():
    result = RealMarketDataIntelligenceWiring(
        market_data_provider=FakeRealMarketDataProvider()
    ).run(symbol="GOLD#")

    assert result["status"] == "READY"
    assert result["symbol"] == "GOLD#"
    assert result["execution"] == "LOCKED_SIMULATION_ONLY"
    assert result["primary_timeframe"] == "H1"
    assert result["modular_intelligence"]["mode"] == "REAL_MARKET_DATA"
    assert result["modular_intelligence"]["data_source"] == "MT5_OHLC_H1"
    assert result["modular_intelligence"]["module_count"] >= 14


def test_runtime_v1_exposes_data_wiring_fields_safely():
    result = RuntimeV1().simulate()

    assert result["symbol"] == "GOLD#"
    assert result["execution"] == "LOCKED_SIMULATION_ONLY"
    assert result["data_status"] in ("READY", "FALLBACK_READY")
    assert "data_source" in result
    assert "primary_timeframe" in result
    assert result["modular_intelligence"]["module_count"] >= 14
