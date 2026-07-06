"""Historical market database foundation for AFIP."""

from afip.market_history.historical_market_observation import HistoricalMarketObservation
from afip.market_history.historical_market_database import HistoricalMarketDatabase
from afip.market_history.historical_market_aggregation import HistoricalMarketAggregator
from afip.market_history.market_signature_history import MarketSignatureHistoryRepository
from afip.market_history.historical_market_runtime import HistoricalMarketRuntime

__all__ = [
    "HistoricalMarketObservation",
    "HistoricalMarketDatabase",
    "HistoricalMarketAggregator",
    "MarketSignatureHistoryRepository",
    "HistoricalMarketRuntime",
]
