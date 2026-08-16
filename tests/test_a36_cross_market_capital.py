import importlib.util
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "tools/afip_a36_cross_market_capital.py"
    spec = importlib.util.spec_from_file_location("a36", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_cross_market_sources_include_fx_and_oil():
    module = _module()
    assert {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "WTI", "BRENT"}.issubset(module.SOURCES)


def test_cross_market_sources_include_us_equity_crypto_metals_and_yields():
    module = _module()
    required = {"SP500", "NASDAQ100", "DOW30", "RUSSELL2000", "VIX",
                "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA",
                "BTCUSD", "ETHUSD", "SILVER", "COPPER", "US02Y", "US10Y"}
    assert required.issubset(module.SOURCES)
    assert module.SOURCE_CATEGORIES["SP500"] == "US_INDEX"
    assert module.SOURCE_CATEGORIES["BTCUSD"] == "CRYPTO"


def test_relationship_reports_one_to_four_closed_bar_lags():
    module = _module()
    gold = [{"time": index * 3600, "close": 100 + index + (index % 3)} for index in range(1100)]
    source = [{"time": index * 3600, "close": 50 + index + (index % 5)} for index in range(1100)]
    result = module._relationship("SP500", gold, source)
    assert result["category"] == "US_INDEX"
    assert [item["lag_closed_bars"] for item in result["lead_lag_h1"]] == [1, 2, 3, 4]
    assert result["status"] == "RESEARCH_READY"


def test_broker_catalog_resolves_common_xm_cash_and_stock_suffixes():
    module = _module()

    class Info:
        def __init__(self, name):
            self.name = name
            self.visible = True
            self.path = "CFD"
            self.description = name
            self.currency_base = "USD"
            self.currency_profit = "USD"

    class MT5:
        def __init__(self):
            self.items = [Info("US500Cash"), Info("AAPL.OQ"), Info("OILCash")]

        def symbols_get(self):
            return self.items

        def symbol_info(self, name):
            return next((item for item in self.items if item.name == name), None)

        def symbol_select(self, name, selected):
            return True

    mt5 = MT5()
    catalog = module._catalog(mt5)
    assert module._resolve_with_evidence(mt5, module.SOURCES["SP500"], catalog)["symbol"] == "US500Cash"
    assert module._resolve_with_evidence(mt5, module.SOURCES["AAPL"], catalog)["symbol"] == "AAPL.OQ"
    assert module._resolve_with_evidence(mt5, module.SOURCES["WTI"], catalog)["symbol"] == "OILCash"


def test_exact_xm_names_and_duplicate_aliases_resolve_one_symbol():
    module = _module()

    class Info:
        def __init__(self, name):
            self.name = name
            self.visible = True

    class MT5:
        def __init__(self):
            self.items = [Info("US500Cash#"), Info("US100Cash#"), Info("Apple")]

        def symbol_info(self, name):
            return next((item for item in self.items if item.name == name), None)

        def symbol_select(self, name, selected):
            return True

    mt5 = MT5()
    catalog = [{"name": item.name} for item in mt5.items]
    assert module._resolve_source(mt5, "SP500", catalog)["symbol"] == "US500Cash#"
    assert module._resolve_source(mt5, "NASDAQ100", catalog)["symbol"] == "US100Cash#"
    assert module._resolve_source(mt5, "AAPL", catalog)["symbol"] == "Apple"


def test_futures_source_selects_nearest_active_contract():
    module = _module()
    future = 4_102_444_800

    class Info:
        visible = False

    class MT5:
        def symbol_info(self, name):
            return Info() if name in {"USDX-SEP30", "USDX-DEC30"} else None

        def symbol_select(self, name, selected):
            return True

    catalog = [{"name": "USDX-SEP30", "expiration_time": future + 1000},
               {"name": "USDX-DEC30", "expiration_time": future + 2000}]
    result = module._resolve_source(MT5(), "DXY", catalog)
    assert result["symbol"] == "USDX-SEP30"
    assert result["method"] == "ACTIVE_FUTURES_CONTRACT"


def test_bond_etfs_are_labeled_as_proxies_not_direct_yields():
    module = _module()
    assert module.SOURCE_CATEGORIES["SHY_1_3Y_BOND_ETF"] == "US_BOND_ETF_PROXY"
    assert module.SOURCE_CATEGORIES["IEF_7_10Y_BOND_ETF"] == "US_BOND_ETF_PROXY"
    assert module.SOURCE_CATEGORIES["TLT_20Y_BOND_ETF"] == "US_BOND_ETF_PROXY"


def test_catalog_blocks_ambiguous_normalized_mapping():
    module = _module()

    class MT5:
        def symbol_info(self, name):
            return None

    catalog = [{"name": "TESTCash"}, {"name": "TEST.OQ"}]
    result = module._resolve_with_evidence(MT5(), ("TEST",), catalog)
    assert result["symbol"] is None
    assert result["method"] == "AMBIGUOUS_BLOCKED"


def test_collection_requires_explicit_approval(tmp_path):
    module = _module()
    try:
        module.collect(tmp_path, False)
    except ValueError as exc:
        assert "approve-active-readonly" in str(exc)
    else:
        raise AssertionError("approval gate was bypassed")


def test_capital_is_candidate_specific_not_hardcoded():
    module = _module()
    broker = {"trade_tick_size": .01, "trade_tick_value_loss": 1.0, "point": .01,
              "volume": .01, "margin_for_volume": 25, "account_currency": "USD"}
    first = module._capital({"average_sl_points": 500, "max_drawdown_r": 5}, broker, 35)
    second = module._capital({"average_sl_points": 1000, "max_drawdown_r": 5}, broker, 35)
    assert first["risk_per_order"] < second["risk_per_order"]
    assert first["recommended_starting_equity"] < second["recommended_starting_equity"]
    assert first["automatic_capital_authority"] is False


def test_no_order_operation_is_called():
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert ".order_send(" not in source
    assert ".order_check(" not in source
