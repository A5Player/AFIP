from __future__ import annotations
import json
from pathlib import Path
from afip.control_center_runtime import ControlCenterRuntime
from afip.dashboard_ui.control_center import render_control_center


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_runtime_authority_projection_uses_real_runtime_files(tmp_path: Path) -> None:
    _write(tmp_path / "runtime/control/final_integration/desired_runtime_state.json", {"state": "RUNNING", "reason": "start_requested"})
    _write(tmp_path / "runtime/control/final_integration/runtime_watchdog_status.json", {"status": "RUNNING", "pid": 222})
    _write(tmp_path / "runtime/execution/sequential_router_status.json", {"status": "RUNNING", "pid": 111})
    _write(tmp_path / "runtime/final_integration_status.json", {"status": "RUNNING", "trading_runtime": {"profiles": []}})
    result = ControlCenterRuntime(tmp_path).snapshot()["runtime_authority"]
    assert result["canonical_lifecycle_authority"] == "tools.afip_final_integration"
    assert result["desired_state"] == "RUNNING"
    assert result["router_pid"] == 111
    assert result["watchdog_pid"] == 222
    assert result["duplicate_process_risk"] == "NONE_DETECTED"
    assert result["mt5_auto_launch_allowed"] is False


def test_runtime_authority_detects_router_running_while_stopped(tmp_path: Path) -> None:
    _write(tmp_path / "runtime/control/final_integration/desired_runtime_state.json", {"state": "STOPPED"})
    _write(tmp_path / "runtime/execution/sequential_router_status.json", {"status": "RUNNING", "pid": 111})
    result = ControlCenterRuntime(tmp_path).snapshot()["runtime_authority"]
    assert result["duplicate_process_risk"] == "ROUTER_RUNNING_WHILE_DESIRED_STOPPED"


def test_control_center_renders_runtime_authority_from_snapshot(tmp_path: Path) -> None:
    _write(tmp_path / "runtime/control/final_integration/desired_runtime_state.json", {"state": "RUNNING", "reason": "start_requested"})
    html = render_control_center(tmp_path)
    assert "Runtime Authority" in html
    assert "tools.afip_final_integration" in html
    assert "START_AFIP.ps1" not in html  # canonical paths remain in snapshot, panel stays concise
    assert "MT5 Auto Launch Allowed" in html
