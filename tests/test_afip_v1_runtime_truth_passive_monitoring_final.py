from __future__ import annotations
import json
from pathlib import Path

from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager


def _config(tmp_path: Path) -> Path:
    terminal = tmp_path / "P1" / "terminal64.exe"
    terminal.parent.mkdir(parents=True)
    terminal.write_text("stub", encoding="utf-8")
    runtime = tmp_path / "runtime" / "profiles" / "p1"
    cfg = {
        "profiles": [{
            "profile_id": "P1", "profile_name": "Conservative", "enabled": True,
            "execution_enabled": True, "research_enabled": True, "launch_mt5": False,
            "mt5_folder": str(terminal.parent), "mt5_terminal": str(terminal),
            "broker": "XM", "server": "TEST", "symbol": "GOLD#",
            "login_env": "AFIP_TEST_LOGIN", "password_env": "AFIP_TEST_PASSWORD",
            "runtime_directory": str(runtime), "database_path": str(runtime / "db.sqlite"),
            "logs_directory": str(runtime / "logs"), "dashboard_path": str(runtime / "dashboard.html"),
            "learning_directory": str(runtime / "learning"), "knowledge_directory": str(runtime / "knowledge"),
            "statistics_directory": str(runtime / "statistics"),
        }]
    }
    path = tmp_path / "four_profile_demo.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_passive_check_never_constructs_mt5_adapter(tmp_path: Path, monkeypatch) -> None:
    cfg = _config(tmp_path)
    called = False
    def forbidden():
        nonlocal called
        called = True
        raise AssertionError("adapter must not be created in passive mode")
    manager = MT5MultiTerminalConnectionManager(cfg, adapter_factory=forbidden)
    monkeypatch.setattr(manager, "_running_terminal_paths", lambda: set())
    report = manager.check(active=False)
    assert called is False
    assert report["monitoring_mode"] == "PASSIVE"
    assert report["profiles"][0]["connection_status"] == "DISCONNECTED"


def test_passive_process_path_maps_to_connected_passive(tmp_path: Path, monkeypatch) -> None:
    cfg = _config(tmp_path)
    manager = MT5MultiTerminalConnectionManager(cfg, adapter_factory=lambda: None)
    terminal = manager.operations.load()[0].mt5_terminal
    monkeypatch.setattr(manager, "_running_terminal_paths", lambda: {manager._normal_path(terminal)})
    report = manager.check(active=False)
    profile = report["profiles"][0]
    assert profile["connection_status"] == "CONNECTED_PASSIVE"
    assert profile["process_alive"] is True
    assert profile["monitoring_mode"] == "PASSIVE"
