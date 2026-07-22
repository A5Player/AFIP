from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from afip.dashboard_ui.research_operations import render_research_operations
from afip.historical_replay_research import AppendOnlyResearchDataset, HistoricalReplayRunner
from afip.runtime_observatory import RuntimeProgressAuthority


def candles(count: int = 4):
    return [
        {"timestamp_utc": f"2026-01-01T00:0{i}:00Z", "open": 100+i, "high": 102+i, "low": 99+i, "close": 101+i, "volume": 10+i}
        for i in range(count)
    ]


def test_replay_progress_callback_updates_every_bar(tmp_path: Path):
    events = []
    runner = HistoricalReplayRunner(dataset=AppendOnlyResearchDataset(tmp_path / "dataset"))
    summary = runner.run(replay_id="R1", research_run_id="RUN1", dataset_version="V1", scenario_id="S1", candles=candles(), progress_callback=events.append)
    assert summary.bars_processed == 4
    assert [event["covered_bars"] for event in events] == [1, 2, 3, 4]
    assert events[-1]["completed"] is True
    assert events[-1]["replay_timestamp_utc"] == "2026-01-01T00:03:00Z"


def test_observatory_classifies_running_waiting_stalled_completed_failed(tmp_path: Path):
    authority = RuntimeProgressAuthority(tmp_path, stalled_after_seconds=10)
    for state in ("RUNNING", "WAITING", "COMPLETED", "FAILED"):
        assert authority.update(state=state, stage="TEST", activity=state)["status"] == state
    stale = authority.update(state="RUNNING", stage="REPLAY", activity="Replay M1")
    stale["heartbeat_utc"] = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat().replace("+00:00", "Z")
    authority.status_path.write_text(json.dumps(stale), encoding="utf-8")
    assert authority.classified()["status"] == "STALLED"


def test_dashboard_reads_single_runtime_progress_authority(tmp_path: Path):
    RuntimeProgressAuthority(tmp_path).update(
        state="RUNNING", stage="HISTORICAL_REPLAY", activity="Replay M5 25/100",
        current_timeframe="M5", replay_processed=25, replay_total=100, replay_percent=25.0,
        replay_speed_bars_per_second=12.5, eta_seconds=6.0,
        current_replay_timestamp_utc="2026-01-01T00:25:00Z",
    )
    html = render_research_operations(tmp_path)
    assert "25.0%" in html
    assert "M5" in html
    assert "12.5 bars/s" in html
    assert "2026-01-01T00:25:00Z" in html
    assert "NOT_RECORDED" not in html


def test_obsolete_capital_display_policy_removed():
    files = [
        Path("afip/dashboard_ui/split_runtime.py"),
        Path("afip/dashboard_ui/authority_snapshot.py"),
        Path("afip/dashboard_ui/research_operations.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "Capital / 0.01" not in text
    assert "capital_per_001" not in text
    assert "capital_per_lot_unit" not in text
