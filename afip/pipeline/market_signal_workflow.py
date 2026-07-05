from afip.market.mt5_market_data_provider import MT5MarketDataProvider
from afip.pipeline.simulation_signal_pipeline import SimulationSignalPipeline


class MarketSignalWorkflow:
    """
    End-to-end safe workflow:
    MarketDataProvider -> SimulationSignalPipeline -> Decision

    Default provider is MT5-aware but falls back to simulation when MT5 is disabled.
    """

    def __init__(self, provider=None, pipeline=None):
        self.provider = provider or MT5MarketDataProvider()
        self.pipeline = pipeline or SimulationSignalPipeline()

    def run(self, symbol: str = "XAUUSD") -> dict:
        snapshot = self.provider.latest_snapshot(symbol)
        result = self.pipeline.run(snapshot)
        result["snapshot"] = snapshot
        return result
