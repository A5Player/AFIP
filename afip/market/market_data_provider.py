class MarketDataProvider:
    def latest_tick(self,symbol):
        return {"symbol":symbol,"bid":None,"ask":None}
