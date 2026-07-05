from afip.market.history_market_data_provider import HistoryMarketDataProvider
def test_safe_history_fallback():
    r=HistoryMarketDataProvider().get_history("XAUUSD","M5",100)
    assert r["source"]=="SIMULATION_HISTORY"
