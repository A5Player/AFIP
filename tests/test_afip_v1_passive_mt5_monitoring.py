from __future__ import annotations
import json
from pathlib import Path

from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager


def _config(tmp_path: Path) -> Path:
    terminal = tmp_path / "P1" / "terminal64.exe"
    terminal.parent.mkdir(parents=True)
    terminal.write_text("stub", encoding="utf-8")
    runtime = tmp_path / "runtime" / "profiles" / "p1"
    path = tmp_path / "four_profile_demo.json"
    root = tmp_path / "runtime" / "profiles" / "p1"
    payload = {"profiles": [{
        "profile_id": "P1", "profile_name": "Conservative", "enabled": True,
        "launch_mt5": False, "mt5_folder": str(terminal.parent), "mt5_terminal": str(terminal),
        "broker": "XM", "server": "XMGlobal-MT5 6", "symbol": "GOLD#",
        "login_env": "AFIP_P1_LOGIN", "password_env": "AFIP_P1_PASSWORD",
        "runtime_directory": str(root), "database_path": str(root / "db/a.sqlite3"),
        "logs_directory": str(root / "logs"), "dashboard_path": str(root / "dashboard/a.html"),
        "learning_directory": str(root / "learning"), "knowledge_directory": str(root / "knowledge"),
        "statistics_directory": str(root / "statistics"), "execution": "LOCKED_SIMULATION_ONLY",
        "direct_execution": False, "live_execution": False
    }]}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_passive_check_never_constructs_mt5_adapter(tmp_path, monkeypatch):
    path = _config(tmp_path)
    manager = MT5MultiTerminalConnectionManager(path, lambda: (_ for _ in ()).throw(AssertionError("adapter must not be created")))
    monkeypatch.setattr(manager, "_terminal_process_alive", lambda _path: False)
    report = manager.check(["P1"], active=False)
    item = report["profiles"][0]
    assert report["monitoring_mode"] == "PASSIVE"
    assert item["connection_status"] == "DISCONNECTED"
    assert item["process_alive"] is False
    assert item["monitoring_mode"] == "PASSIVE"


def test_passive_check_preserves_last_values_as_snapshot(tmp_path, monkeypatch):
    path = _config(tmp_path)
    manager = MT5MultiTerminalConnectionManager(path)
    profile = manager.operations.load()[0]
    profile.runtime_directory.mkdir(parents=True, exist_ok=True)
    (profile.runtime_directory / "mt5_health.json").write_text(json.dumps({
        "checked_at_utc": "2026-07-26T09:00:00+00:00", "balance": 900.0,
        "bid": 4052.54, "ask": 4053.30, "account": "****1234", "server": "XMGlobal-MT5 6",
    }), encoding="utf-8")
    monkeypatch.setattr(manager, "_terminal_process_alive", lambda _path: False)
    item = manager.check(["P1"], active=False)["profiles"][0]
    assert item["connection_status"] == "DISCONNECTED"
    assert item["balance"] == 900.0
    assert item["evidence_kind"] == "LAST_SNAPSHOT"
    assert item["snapshot_checked_at_utc"] == "2026-07-26T09:00:00+00:00"
    assert item["trade_allowed"] is False
