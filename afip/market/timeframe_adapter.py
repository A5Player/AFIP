from afip.timeframe_registry import get_minutes, get_supported_timeframes


class TimeframeAdapter:
    DEFAULTS = {name: get_minutes(name) for name in get_supported_timeframes()}

    def to_minutes(self, timeframe: str) -> int:
        return get_minutes(timeframe)
