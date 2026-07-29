from datetime import datetime, timezone
from types import SimpleNamespace

from afip.mt5_historical_integration.mt5_gateway import MetaTrader5ReadOnlyGateway


class FakeMT5:
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 60
    TIMEFRAME_H4 = 240
    TIMEFRAME_D1 = 1440

    def __init__(self, times):
        # MT5 position zero is newest, larger positions are older.
        self.times = list(sorted(times, reverse=True))
        self.calls = []

    def symbol_select(self, symbol, enabled):
        return True

    def terminal_info(self):
        return SimpleNamespace(maxbars=100000)

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.calls.append((start_pos, count))
        values = self.times[start_pos:start_pos + count]
        return [{"time": value, "open": 1.0, "high": 2.0, "low": 0.5,
                 "close": 1.5, "tick_volume": 1, "spread": 1, "real_volume": 0}
                for value in values]


def test_discovery_walks_multiple_bounded_position_blocks():
    base = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
    times = [base + minute * 60 for minute in range(25050)]
    fake = FakeMT5(times)
    gateway = MetaTrader5ReadOnlyGateway(fake)
    gateway._broker_time_offset_seconds = 0

    evidence = gateway.discover_history("GOLD#", "M1", block_size=10000)

    assert evidence.status == "READY"
    assert evidence.bars_observed == 25050
    assert evidence.exhausted_history is True
    assert evidence.probes_completed == 3
    assert evidence.earliest_available_utc == "2024-01-01T00:00:00+00:00"
    assert fake.calls == [(0, 10000), (10000, 10000), (20000, 10000)]


def test_discovery_reports_no_data_without_inventing_earliest_timestamp():
    fake = FakeMT5([])
    gateway = MetaTrader5ReadOnlyGateway(fake)
    gateway._broker_time_offset_seconds = 0

    evidence = gateway.discover_history("GOLD#", "M1")

    assert evidence.status == "NO_DATA"
    assert evidence.earliest_available_utc is None
    assert evidence.bars_observed == 0
    assert evidence.reason == "history_not_returned"


def test_earliest_available_uses_discovery_result():
    base = int(datetime(2025, 6, 1, tzinfo=timezone.utc).timestamp())
    fake = FakeMT5([base, base + 60, base + 120])
    gateway = MetaTrader5ReadOnlyGateway(fake)
    gateway._broker_time_offset_seconds = 0

    assert gateway.earliest_available("GOLD#", "M1") == "2025-06-01T00:00:00+00:00"
    assert gateway.last_history_discovery["bars_observed"] == 3
