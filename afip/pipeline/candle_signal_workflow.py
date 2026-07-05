from afip.market.candle_snapshot_builder import CandleSnapshotBuilder
from afip.pipeline.simulation_signal_pipeline import SimulationSignalPipeline

class CandleSignalWorkflow:
    def __init__(self, snapshot_builder=None, signal_pipeline=None):
        self.snapshot_builder = snapshot_builder or CandleSnapshotBuilder()
        self.signal_pipeline = signal_pipeline or SimulationSignalPipeline()

    def run(self, symbol: str, candles, spread: float, source: str = "CANDLE_SIMULATION") -> dict:
        snapshot = self.snapshot_builder.build(symbol=symbol, candles=candles, spread=spread, source=source)
        result = self.signal_pipeline.run(snapshot)
        result["snapshot"] = snapshot
        return result
