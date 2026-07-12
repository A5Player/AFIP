from __future__ import annotations

import json
from pathlib import Path

import pytest

from afip.locked_simulation_runtime import LockedSimulationConfig, LockedSimulationRunner


def result(action: str = "BUY", confidence: float = 90.0) -> dict:
    return {
        "status": "OK",
        "mode": "SIMULATION",
        "symbol": "GOLD#",
        "data_status": "READY",
        "data_source": "MT5_OHLC_H1",
        "primary_timeframe": "H1",
        "multi_timeframe_confluence": {"direction": "BUY", "confidence": 88.0},
        "decision": {"action": action, "confidence": confidence, "reason": "test_reason"},
        "trading_cost_intelligence": {"status": "READY", "spread_points": 20.0},
        "risk": {"allowed": True, "reasons": ["risk_pass"]},
        "order": {"status": "SIMULATION_ORDER_READY", "action": action, "lot": 0.01},
    }


def config(tmp_path: Path, cycles: int = 1) -> LockedSimulationConfig:
    return LockedSimulationConfig(
        interval_seconds=1.0,
        maximum_cycles=cycles,
        runtime_directory=tmp_path,
        refresh_dashboard=False,
    )


def test_config_rejects_unsafe_interval() -> None:
    with pytest.raises(ValueError, match="interval_seconds_must_be_at_least_one"):
        LockedSimulationConfig(interval_seconds=0).validate()


def test_runner_preserves_execution_lock(tmp_path: Path) -> None:
    summary = LockedSimulationRunner(config(tmp_path), simulate=result, sleep=lambda _: None).run()
    assert summary.execution == "LOCKED_SIMULATION_ONLY"
    assert summary.order_status == "NO_ORDER_SENT"
    assert summary.live_execution is False
    assert summary.direct_execution is False


def test_runner_records_snapshot(tmp_path: Path) -> None:
    LockedSimulationRunner(config(tmp_path), simulate=result, sleep=lambda _: None).run()
    event = json.loads((tmp_path / "events.jsonl").read_text().splitlines()[0])
    assert event["symbol"] == "GOLD#"
    assert event["decision_action"] == "BUY"
    assert event["order_status"] == "NO_ORDER_SENT"


def test_runner_deduplicates_identical_snapshots(tmp_path: Path) -> None:
    summary = LockedSimulationRunner(config(tmp_path, 2), simulate=result, sleep=lambda _: None).run()
    assert summary.completed_cycles == 2
    assert summary.recorded_snapshots == 1
    assert summary.duplicate_snapshots == 1
    assert len((tmp_path / "events.jsonl").read_text().splitlines()) == 1


def test_runner_records_changed_snapshot(tmp_path: Path) -> None:
    values = iter((result("BUY"), result("SELL")))
    summary = LockedSimulationRunner(config(tmp_path, 2), simulate=lambda: next(values), sleep=lambda _: None).run()
    assert summary.recorded_snapshots == 2
    assert summary.duplicate_snapshots == 0


def test_runner_records_cycle_failure_and_continues(tmp_path: Path) -> None:
    calls = 0
    def simulate():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary_failure")
        return result()
    summary = LockedSimulationRunner(config(tmp_path, 2), simulate=simulate, sleep=lambda _: None).run()
    assert summary.failed_cycles == 1
    assert summary.completed_cycles == 2
    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert json.loads(lines[0])["event"] == "cycle_failure"


def test_runner_refreshes_dashboard_when_enabled(tmp_path: Path) -> None:
    refreshes = []
    cfg = LockedSimulationConfig(1.0, 1, tmp_path, True)
    LockedSimulationRunner(cfg, simulate=result, dashboard_builder=lambda: refreshes.append(True), sleep=lambda _: None).run()
    assert refreshes == [True]


def test_summary_and_status_are_written_atomically(tmp_path: Path) -> None:
    LockedSimulationRunner(config(tmp_path), simulate=result, sleep=lambda _: None).run()
    summary = json.loads((tmp_path / "acceptance_summary.json").read_text())
    status = json.loads((tmp_path / "status.json").read_text())
    assert summary["completed_cycles"] == 1
    assert status["runtime_state"] == "STOPPED"
    assert status["execution"] == "LOCKED_SIMULATION_ONLY"
