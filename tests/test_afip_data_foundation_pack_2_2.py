from datetime import datetime, timezone
from types import SimpleNamespace

from afip.mt5_historical_integration.mt5_gateway import MetaTrader5ReadOnlyGateway


class BrokerTimeFakeMT5:
    TIMEFRAME_M1 = 1

    def __init__(self, now_epoch: int):
        self.now_epoch = now_epoch
        self.pos_calls = []

    def terminal_info(self):
        return SimpleNamespace(maxbars=100000)

    def symbol_select(self, symbol, enabled):
        return True

    def copy_rates_from_pos(self, symbol, timeframe, pos, count):
        self.pos_calls.append((symbol, timeframe, pos, count))
        # Broker timestamps are UTC+3 encoded into epoch values.
        if pos == 0 and count == 2:
            return [
                {"time": self.now_epoch + 3 * 3600 - 60},
                {"time": self.now_epoch + 3 * 3600},
            ]
        if pos == 1 and count == 1:
            return [{"time": self.now_epoch + 3 * 3600 - 60}]
        return [
            {"time": self.now_epoch + 3 * 3600 - 86400},
            {"time": self.now_epoch + 3 * 3600 - 60},
            {"time": self.now_epoch + 3 * 3600},
        ]

    def copy_rates_range(self, symbol, timeframe, start, end):
        return [
            {"time": self.now_epoch + 3 * 3600 - 120, "open": 1, "high": 2, "low": 0.5,
             "close": 1.5, "tick_volume": 10, "spread": 20, "real_volume": 0},
            {"time": self.now_epoch + 3 * 3600 - 60, "open": 1.5, "high": 2.2, "low": 1,
             "close": 2, "tick_volume": 11, "spread": 21, "real_volume": 0},
        ]


def test_broker_server_time_is_normalized_to_utc(monkeypatch):
    now = datetime(2026, 7, 28, 14, 16, tzinfo=timezone.utc)
    now_epoch = int(now.timestamp())
    fake = BrokerTimeFakeMT5(now_epoch)
    gateway = MetaTrader5ReadOnlyGateway(fake)
    monkeypatch.setattr(gateway, "_now_utc", lambda: now)

    latest = gateway.latest_closed_bar("GOLD#", "M1")
    earliest = gateway.earliest_available("GOLD#", "M1")

    assert latest == "2026-07-28T14:15:00+00:00"
    assert earliest == "2026-07-27T14:16:00+00:00"
    assert gateway.broker_time_offset_seconds == 10800
    assert earliest < latest


def test_earliest_available_scans_terminal_history_not_current_bar(monkeypatch):
    now = datetime(2026, 7, 28, 14, 16, tzinfo=timezone.utc)
    fake = BrokerTimeFakeMT5(int(now.timestamp()))
    gateway = MetaTrader5ReadOnlyGateway(fake)
    monkeypatch.setattr(gateway, "_now_utc", lambda: now)

    gateway.earliest_available("GOLD#", "M1")

    assert any(pos == 0 and count > 2 for _, _, pos, count in fake.pos_calls)


def test_fetch_applies_same_time_normalization(monkeypatch):
    now = datetime(2026, 7, 28, 14, 16, tzinfo=timezone.utc)
    fake = BrokerTimeFakeMT5(int(now.timestamp()))
    gateway = MetaTrader5ReadOnlyGateway(fake)
    monkeypatch.setattr(gateway, "_now_utc", lambda: now)

    rows = gateway.fetch(
        "GOLD#", "M1", "2026-07-28T14:00:00+00:00", "2026-07-28T14:15:00+00:00", 50000
    )

    assert rows[0]["timestamp_utc"] == "2026-07-28T14:14:00+00:00"
    assert rows[-1]["timestamp_utc"] == "2026-07-28T14:15:00+00:00"
    assert rows[-1]["next_start_utc"] == "2026-07-28T14:15:01+00:00"
