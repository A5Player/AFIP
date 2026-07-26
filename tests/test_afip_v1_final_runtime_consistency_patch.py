from __future__ import annotations

import json
from pathlib import Path

from afip.automatic_research_runtime.runtime import AutomaticResearchRuntime
from afip.final_integration import FinalIntegrationRuntime


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_stopped_processes_override_stale_running_snapshots(tmp_path: Path, monkeypatch) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    monkeypatch.setattr(
        runtime,
        "_trading",
        lambda command: {
            "status": "READY",
            "router": {"running": False, "pid": None, "state": "RUNNING"},
            "profiles": [{"profile_id": "P1", "runtime_state": "STOPPED"}],
        },
    )
    write_json(tmp_path / "runtime/research/research_engine_status.json", {"status": "RUNNING", "process_id": 123})
    write_json(tmp_path / "runtime/research/runtime_observatory_status.json", {"status": "RUNNING", "process_id": 456})
    write_json(tmp_path / "runtime/dashboard/dashboard_monitor_status.json", {"status": "RUNNING", "process_id": 789})

    value = runtime.status().as_dict()

    assert value["status"] == "STOPPED"
    assert value["trading_runtime"]["router"]["state"] == "STOPPED"
    assert value["research_runtime"]["engine"]["status"] == "STOPPED"
    assert value["research_runtime"]["observatory"]["status"] == "STOPPED"
    assert value["research_runtime"]["observatory"]["process_id"] is None
    assert value["dashboard"]["status"]["status"] == "STOPPED"


def test_stop_persists_canonical_stopped_snapshots(tmp_path: Path, monkeypatch) -> None:
    runtime = FinalIntegrationRuntime(tmp_path)
    monkeypatch.setattr(runtime, "_trading", lambda command: {"status": "READY", "profiles": []})
    write_json(tmp_path / "runtime/research/research_engine_status.json", {"status": "RUNNING", "process_id": 123})
    write_json(tmp_path / "runtime/research/runtime_observatory_status.json", {"status": "RUNNING", "process_id": 456})
    write_json(tmp_path / "runtime/dashboard/dashboard_monitor_status.json", {"status": "RUNNING", "process_id": 789, "cycles": 7})

    runtime.stop()

    engine = json.loads((tmp_path / "runtime/research/research_engine_status.json").read_text())
    observatory = json.loads((tmp_path / "runtime/research/runtime_observatory_status.json").read_text())
    dashboard = json.loads((tmp_path / "runtime/dashboard/dashboard_monitor_status.json").read_text())
    assert engine["status"] == "STOPPED" and engine["process_id"] is None
    assert observatory["status"] == "STOPPED" and observatory["stage"] == "STOPPED"
    assert dashboard["status"] == "STOPPED" and dashboard["cycles"] == 7


def test_non_ohlc_runtime_records_are_skipped_not_rejected(tmp_path: Path) -> None:
    write_json(tmp_path / "runtime/research/status.json", {"status": "RUNNING", "heartbeat_utc": "2026-07-26T00:00:00Z"})
    write_json(
        tmp_path / "data/historical/bars.json",
        {"records": [
            {"timestamp_utc": "2026-07-26T00:00:00Z", "timeframe": "M1", "open": 1, "high": 2, "low": 0.5, "close": 1.5},
            {"timestamp_utc": "2026-07-26T00:01:00Z", "timeframe": "M1", "open": 1, "high": 0, "low": 2, "close": 1.5},
        ]},
    )

    bars, _, _, rejected = AutomaticResearchRuntime(tmp_path).discover_bars()
    index = json.loads((tmp_path / "runtime/research/research_file_index.json").read_text())

    assert len(bars) == 1
    assert rejected == 1
    status_entry = index["files"]["runtime/research/status.json"]
    assert status_entry["classification"] == "NON_OHLC_SKIPPED"
    assert status_entry["rejected_records"] == 0
    assert index["invalid_ohlc_records_rejected"] == 1
    assert index["non_ohlc_files_skipped"] >= 1
