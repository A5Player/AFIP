from types import SimpleNamespace

from afip.market.mt5_market_data_provider import MT5MarketDataProvider
from afip.symbol.mt5_symbol_resolver import MT5SymbolResolver


class FakeMT5Client:
    TIMEFRAME_M1 = "M1"

    def __init__(self):
        self.selected = []

    def initialize(self):
        return True

    def symbols_get(self):
        return [SimpleNamespace(name="XAUUSD"), SimpleNamespace(name="GOLD#"), SimpleNamespace(name="EURUSD")]

    def symbol_select(self, symbol, enabled):
        self.selected.append(symbol)
        return symbol == "GOLD#"

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(bid=3300.0, ask=3300.31, last=3300.1, time=1)

    def symbol_info(self, symbol):
        return SimpleNamespace(digits=2, point=0.01, trade_contract_size=100)

    def account_info(self):
        return SimpleNamespace(login=1, server="XMGlobal-MT5 6", balance=100, equity=100, margin=0, margin_free=100, currency="USD")

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        return []


class FakeAdapter:
    def __init__(self):
        self.mt5_client = FakeMT5Client()
        self.enabled = True
        self.initialized = True

    def is_available(self):
        return True

    def symbol_select(self, symbol):
        return {"symbol": symbol, "selected": symbol == "GOLD#", "reason": "selected" if symbol == "GOLD#" else "symbol_select_failed"}


def test_resolver_prefers_gold_hash():
    adapter = FakeAdapter()
    result = MT5SymbolResolver(adapter, preferred_symbol="GOLD#").resolve("XAUUSD")
    assert result["resolved"] == "GOLD#"
    assert result["selected"] is True


def test_connection_check_reports_gold_hash():
    from afip.broker.mt5_adapter import MT5Adapter

    adapter = MT5Adapter(mt5_client=FakeMT5Client(), enabled=True)
    provider = MT5MarketDataProvider(adapter=adapter)
    result = provider.connection_check("XAUUSD")
    assert result["symbol"] == "GOLD#"
    assert result["requested_symbol"] == "XAUUSD"
    assert result["symbol_select"]["selected"] is True
