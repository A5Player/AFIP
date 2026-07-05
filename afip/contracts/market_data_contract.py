from typing import Protocol

class MarketDataContract(Protocol):
    def latest_snapshot(self, symbol: str = "XAUUSD") -> dict:
        ...
