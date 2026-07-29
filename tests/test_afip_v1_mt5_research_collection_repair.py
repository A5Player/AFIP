from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.automatic_research_runtime import AutomaticResearchRuntime


def _bar(timestamp: datetime, timeframe: str = "M1") -> dict[str, object]:
    return {
        "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "open": 2300.0,
        "high": 2301.0,
        "low": 2299.0,
        "close": 2300.5,
        "volume": 10.0,
        "timeframe": timeframe,
        "source": "TEST",
    }


def test_populated_m1_does_not_suppress_missing_timeframe_mt5_collection(tmp_path, monkeypatch):
    runtime = AutomaticResearchRuntime(tmp_path)
    start = datetime.now(timezone.utc) - timedelta(minutes=101)
    local_bars = [_bar(start + timedelta(minutes=index)) for index in range(101)]
    collected = [_bar(datetime.now(timezone.utc) - timedelta(minutes=1), timeframe) for timeframe in ("M1", "M5", "M15", "M30", "H1", "H4", "D1")]
    calls: list[int] = []

    monkeypatch.setattr(runtime, "discover_bars", lambda: (local_bars, 1, len(local_bars), 0))
    monkeypatch.setattr(runtime, "collect_mt5_bars", lambda maximum_per_timeframe=5000: calls.append(maximum_per_timeframe) or collected)
    monkeypatch.setattr(runtime, "persist_historical_bars", lambda bars: (len(tuple(bars)), 0))

    summary = runtime.run(maximum_replay_bars=1)

    assert summary.mt5_collection_attempted is True
    assert summary.mt5_bars_collected == 7
    assert calls == [5000]
    assert "m5_data_missing" in summary.mt5_collection_reasons
    assert "D1" in summary.mt5_timeframes_requested


def test_collection_can_still_be_explicitly_disabled(tmp_path, monkeypatch):
    runtime = AutomaticResearchRuntime(tmp_path)
    start = datetime.now(timezone.utc) - timedelta(minutes=101)
    local_bars = [_bar(start + timedelta(minutes=index)) for index in range(101)]

    monkeypatch.setattr(runtime, "discover_bars", lambda: (local_bars, 1, len(local_bars), 0))
    monkeypatch.setattr(runtime, "collect_mt5_bars", lambda maximum_per_timeframe=5000: (_ for _ in ()).throw(AssertionError("must not collect")))

    summary = runtime.run(collect_mt5_when_needed=False, maximum_replay_bars=1)

    assert summary.mt5_collection_attempted is False
    assert "m5_data_missing" in summary.mt5_collection_reasons
