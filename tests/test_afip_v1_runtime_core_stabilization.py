from __future__ import annotations

import json
import os
from pathlib import Path

from afip.operational_runtime import OperationalRuntime
from tools import afip_verify_account_isolation as isolation

ROOT = Path(__file__).resolve().parents[1]


def test_supervisor_lock_is_atomic_and_single_owner(tmp_path: Path) -> None:
    first = OperationalRuntime(tmp_path)
    second = OperationalRuntime(tmp_path)
    assert first._acquire_supervisor_lock() is True
    assert second._acquire_supervisor_lock() is False
    owner = json.loads(first.lock_path.read_text(encoding="utf-8"))
    assert owner["pid"] == os.getpid()
    first._release_supervisor_lock()
    assert not first.lock_path.exists()


def test_stale_supervisor_lock_is_reclaimed(tmp_path: Path, monkeypatch) -> None:
    runtime = OperationalRuntime(tmp_path)
    runtime.directory.mkdir(parents=True)
    runtime.lock_path.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
    monkeypatch.setattr("afip.operational_runtime.process_alive", lambda pid: False)
    assert runtime._acquire_supervisor_lock() is True
    runtime._release_supervisor_lock()


def test_cli_has_one_lifecycle_owner_and_does_not_start_router_directly() -> None:
    text = (ROOT / "tools" / "afip_operational_runtime.py").read_text(encoding="utf-8")
    start_block = text.split('if args.command == "start":', 1)[1].split('if args.command == "stop":', 1)[0]
    assert "runtime.start_background()" in start_block
    assert "afip_demo_execution_control" not in start_block
    assert '"mt5_auto_launch": False' in start_block


def test_account_isolation_requires_manually_running_terminal(monkeypatch, tmp_path: Path) -> None:
    class Profile:
        profile_id = "P1"
        enabled = True
        execution_enabled = True
        login = "123456"
        password_configured = True
        mt5_folder = Path(r"C:\\XM Global MT5 P1")
        mt5_terminal = mt5_folder / "terminal64.exe"
        server = "XMGlobal-MT5 6"
        password_env = "AFIP_P1_PASSWORD"

    monkeypatch.setattr(isolation.FourProfileOperationalRuntime, "load", lambda self: (Profile(),))
    monkeypatch.setattr(isolation, "running_terminal_paths", lambda: [])
    monkeypatch.setattr(isolation, "is_windows", lambda: True)
    report = isolation.verify(tmp_path / "config.json")
    assert report["safe_to_start"] is False
    assert report["mt5_auto_launch"] is False
    assert report["profiles"][0]["reason"] == "mt5_terminal_not_running_manual_start_required"


def test_duplicate_terminal_process_is_blocked(monkeypatch, tmp_path: Path) -> None:
    class Profile:
        profile_id = "P1"
        enabled = True
        execution_enabled = True
        login = "123456"
        password_configured = True
        mt5_folder = Path(r"C:\\XM Global MT5 P1")
        mt5_terminal = mt5_folder / "terminal64.exe"
        server = "XMGlobal-MT5 6"
        password_env = "AFIP_P1_PASSWORD"

    terminal = isolation.normalize(str(Profile.mt5_terminal))
    monkeypatch.setattr(isolation.FourProfileOperationalRuntime, "load", lambda self: (Profile(),))
    monkeypatch.setattr(isolation, "running_terminal_paths", lambda: [terminal, terminal])
    monkeypatch.setattr(isolation, "is_windows", lambda: True)
    report = isolation.verify(tmp_path / "config.json")
    assert report["safe_to_start"] is False
    assert report["profiles"][0]["reason"] == "duplicate_mt5_terminal_process"
