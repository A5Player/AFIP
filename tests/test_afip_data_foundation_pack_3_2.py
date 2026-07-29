from datetime import datetime, timezone
from types import SimpleNamespace

from afip.mt5_historical_integration.mt5_gateway import MetaTrader5ReadOnlyGateway


def _bar(iso_utc: str):
    # Simulate XM-style epochs encoded three hours ahead of UTC.
    raw = int(datetime.fromisoformat(iso_utc).timestamp()) + 10800
    return {
        "time": raw,
        "open": 1.0,
        "high": 2.0,
        "low": 0.5,
        "close": 1.5,
        "tick_volume": 10,
        "spread": 2,
        "real_volume": 0,
    }


class PositionOnlyMT5:
    TIMEFRAME_M1 = 1

    def __init__(self):
        self.values = [
            _bar("2026-01-01T00:02:00+00:00"),
            _bar("2026-01-01T00:01:00+00:00"),
            _bar("2026-01-01T00:00:00+00:00"),
        ]

    def symbol_select(self, *args):
        return True

    def terminal_info(self):
        return SimpleNamespace(maxbars=100000)

    def copy_rates_range(self, *args):
        return []

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return self.values[start_pos:start_pos + count]


def test_fetch_falls_back_to_position_cache_when_range_api_is_empty():
    fake = PositionOnlyMT5()
    gateway = MetaTrader5ReadOnlyGateway(fake)
    gateway._broker_time_offset_seconds = 10800
    rows = gateway.fetch(
        "GOLD#",
        "M1",
        "2026-01-01T00:00:00+00:00",
        "2026-01-01T00:02:00+00:00",
        50000,
    )
    assert [row["timestamp_utc"] for row in rows] == [
        "2026-01-01T00:00:00+00:00",
        "2026-01-01T00:01:00+00:00",
        "2026-01-01T00:02:00+00:00",
    ]
    assert rows[-1]["next_start_utc"] == "2026-01-01T00:02:01+00:00"
