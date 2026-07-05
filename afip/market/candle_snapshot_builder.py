from afip.market.candle_normalizer import CandleNormalizer

class CandleSnapshotBuilder:
    def __init__(self, normalizer=None):
        self.normalizer = normalizer or CandleNormalizer()

    def build(self, symbol: str, candles, spread: float, source: str = "CANDLES") -> dict:
        normalized = self.normalizer.normalize_many(candles)
        return {
            "symbol": symbol,
            "closes": [c.close for c in normalized],
            "highs": [c.high for c in normalized],
            "lows": [c.low for c in normalized],
            "opens": [c.open for c in normalized],
            "volumes": [c.volume for c in normalized],
            "spread": spread,
            "source": source,
            "candle_count": len(normalized),
        }
