from afip.broker.mt5_history_adapter import MT5HistoryAdapter

class HistoryMarketDataProvider:
    def __init__(self,adapter=None):
        self.adapter=adapter or MT5HistoryAdapter()

    def get_history(self,symbol,timeframe,count=500):
        data=self.adapter.copy_rates(symbol,timeframe,count)
        if data is None:
            return {"source":"SIMULATION_HISTORY","candles":[]}
        return {"source":"MT5_HISTORY","candles":data}
