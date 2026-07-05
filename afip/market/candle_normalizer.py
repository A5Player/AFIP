from afip.models.candle import Candle

class CandleNormalizer:
    def normalize_one(self, raw) -> Candle:
        if isinstance(raw, Candle):
            return raw

        if isinstance(raw, dict):
            def getter(key, default=None):
                return raw.get(key, default)
        else:
            def getter(key, default=None):
                return getattr(raw, key, default)

        candle = Candle(
            time=getter("time", None),
            open=float(getter("open", 0.0)),
            high=float(getter("high", 0.0)),
            low=float(getter("low", 0.0)),
            close=float(getter("close", 0.0)),
            volume=float(getter("tick_volume", getter("volume", 0.0))),
        )
        if not candle.is_valid():
            raise ValueError(f"Invalid candle data: {raw}")
        return candle

    def normalize_many(self, rows) -> list:
        return [self.normalize_one(row) for row in rows]
