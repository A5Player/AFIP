from afip.market.candle_snapshot_builder import CandleSnapshotBuilder

class CandleBatchProcessor:
    def __init__(self, snapshot_builder=None):
        self.snapshot_builder = snapshot_builder or CandleSnapshotBuilder()

    def build_timeframe_snapshots(self, symbol: str, timeframe_candles: dict, spread: float) -> dict:
        snapshots = {}
        for timeframe, candles in timeframe_candles.items():
            snapshots[timeframe] = self.snapshot_builder.build(
                symbol=symbol,
                candles=candles,
                spread=spread,
                source=f"CANDLE_BATCH_{timeframe}",
            )
        return snapshots
