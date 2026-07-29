from afip.mt5_historical_integration import HistoricalDataDashboard, ResumableMT5HistoricalProvider
from afip.runtime_standard_adapter import BackfillRequest


class Gateway:
    def __init__(self, rows):
        self.rows = rows
        self.called = False
    def available_symbols(self): return ("GOLD#",)
    def earliest_available(self, symbol, timeframe): return "2026-01-01T00:00:00+00:00"
    def latest_closed_bar(self, symbol, timeframe): return "2026-01-01T00:03:00+00:00"
    def fetch(self, symbol, timeframe, start, end, maximum_bars):
        if self.called: return []
        self.called = True
        return self.rows


def row(ts, nxt, o=1, h=2, l=0, c=1.5):
    return {"timestamp_utc": ts, "next_start_utc": nxt, "open": o, "high": h, "low": l, "close": c, "volume": 10}


def test_quality_rejects_impossible_ohlc_and_reports_gap(tmp_path):
    rows = [
        row("2026-01-01T00:00:00+00:00", "2026-01-01T00:01:00+00:00"),
        row("2026-01-01T00:02:00+00:00", "2026-01-01T00:03:00+00:00"),
        row("2026-01-01T00:03:00+00:00", "2026-01-01T00:04:00+00:00", o=5, h=4, l=1, c=3),
    ]
    result = ResumableMT5HistoricalProvider(tmp_path).run(BackfillRequest("D1", "GOLD#", "M1"), Gateway(rows))
    assert result.bars_persisted == 2
    assert result.bars_rejected == 1
    assert result.missing_interval_count == 1
    assert result.quality_status == "FAIL"
    assert result.bytes_written > 0


def test_dashboard_is_not_started_without_runtime_evidence(tmp_path):
    view = HistoricalDataDashboard(tmp_path).snapshot("UNKNOWN")
    assert view["status"] == "NOT_STARTED"
    assert view["reason"] == "loader_has_not_been_started"
    assert view["bars_accepted"] == 0


def test_dashboard_reads_real_loader_evidence(tmp_path):
    rows = [row("2026-01-01T00:00:00+00:00", "2026-01-01T00:04:00+00:00")]
    ResumableMT5HistoricalProvider(tmp_path).run(BackfillRequest("D2", "GOLD#", "M1"), Gateway(rows))
    view = HistoricalDataDashboard(tmp_path).snapshot("D2")
    assert view["instrument"] == "GOLD#"
    assert view["timeframe"] == "M1"
    assert view["bars_received"] == 1
    assert view["bars_accepted"] == 1
    assert view["total_dataset_bytes"] > 0
    assert len(view["dashboard_checksum"]) == 64
