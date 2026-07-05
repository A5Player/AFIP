class TimeframeAdapter:
    DEFAULTS = {"M1":1,"M5":5,"M15":15,"M30":30,"H1":60,"H4":240,"D1":1440}

    def to_minutes(self, timeframe: str) -> int:
        key = timeframe.upper()
        if key not in self.DEFAULTS:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return self.DEFAULTS[key]
