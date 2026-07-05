class MT5HistoryAdapter:
    """Safe history adapter. Returns None when MT5 is unavailable."""
    def __init__(self, mt5_client=None, enabled=False):
        self.mt5_client=mt5_client
        self.enabled=enabled

    def copy_rates(self,symbol,timeframe,count=500):
        if not self.enabled or self.mt5_client is None:
            return None
        return self.mt5_client.copy_rates_from_pos(symbol,timeframe,0,count)
