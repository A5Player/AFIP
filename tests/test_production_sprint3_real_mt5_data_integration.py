from collections import namedtuple

from afip.broker.mt5_adapter import MT5Adapter
from afip.market.mt5_market_data_provider import MT5MarketDataProvider


Tick = namedtuple("Tick", "bid ask last time")
SymbolInfo = namedtuple("SymbolInfo", "digits point trade_contract_size")
AccountInfo = namedtuple("AccountInfo", "login server balance equity margin margin_free currency")


class FakeMT5Client:
    TIMEFRAME_M1 = "M1"
    TIMEFRAME_M5 = "M5"
    TIMEFRAME_M15 = "M15"
    TIMEFRAME_H1 = "H1"
    TIMEFRAME_H4 = "H4"
    TIMEFRAME_D1 = "D1"

    def initialize(self):
        return True

    def symbol_select(self, symbol, enabled):
        return symbol == "XAUUSD" and enabled is True

    def symbol_info_tick(self, symbol):
        return Tick(bid=2300.10, ask=2300.28, last=2300.20, time=123456)

    def symbol_info(self, symbol):
        return SymbolInfo(digits=2, point=0.01, trade_contract_size=100)

    def account_info(self):
        return AccountInfo(login=123, server="Demo", balance=1000.0, equity=1005.0, margin=10.0, margin_free=995.0, currency="USD")

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        return [
            {"time": 1, "open": 2300.0, "high": 2301.0, "low": 2299.5, "close": 2300.5, "tick_volume": 100},
            {"time": 2, "open": 2300.5, "high": 2302.0, "low": 2300.0, "close": 2301.5, "tick_volume": 120},
        ]


def test_mt5_adapter_reads_tick_account_symbol_and_rates():
    adapter = MT5Adapter(mt5_client=FakeMT5Client(), enabled=True)

    assert adapter.initialize()["initialized"] is True
    assert adapter.symbol_select("XAUUSD")["selected"] is True
    assert adapter.latest_tick("XAUUSD")["available"] is True
    assert adapter.symbol_info("XAUUSD")["digits"] == 2
    assert adapter.account_info()["server"] == "Demo"
    rates = adapter.copy_rates("XAUUSD", "M5", count=2)
    assert rates["available"] is True
    assert len(rates["rates"]) == 2


def test_mt5_market_data_provider_builds_timeframe_snapshots():
    provider = MT5MarketDataProvider(adapter=MT5Adapter(mt5_client=FakeMT5Client(), enabled=True))
    check = provider.connection_check("XAUUSD")
    assert check["status"] == "READY"
    assert check["execution"] == "LOCKED_SIMULATION_ONLY"

    result = provider.timeframe_snapshots("XAUUSD", timeframes=("M1", "M5"), count=2)
    assert result["source"] == "MT5_OHLC"
    assert result["timeframes"]["M1"]["source"] == "MT5_OHLC_M1"
    assert result["timeframes"]["M5"]["candle_count"] == 2


def test_mt5_market_data_provider_falls_back_safely_when_disabled():
    provider = MT5MarketDataProvider(adapter=MT5Adapter(enabled=False))
    check = provider.connection_check("XAUUSD")
    assert check["status"] == "FALLBACK_READY"

    snapshot = provider.latest_snapshot("XAUUSD")
    assert snapshot["source"] == "SIMULATION_FALLBACK"
    assert snapshot["fallback_reason"] == "mt5_adapter_disabled"
