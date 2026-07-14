from __future__ import annotations

import json
from pathlib import Path

from afip.dashboard_ui.launcher import default_dashboard_record
from afip.dashboard_ui.runtime import DashboardUIRuntime
from afip.four_profile_operations.runtime import FourProfileSupervisor


def test_dashboard_places_operational_profiles_before_technical_panels(tmp_path, monkeypatch):
    config = tmp_path / "profiles.json"
    profiles = []
    for index in range(1, 5):
        runtime = tmp_path / f"p{index}"
        runtime.mkdir()
        terminal = tmp_path / f"terminal{index}.exe"
        terminal.write_text("", encoding="utf-8")
        profiles.append({
            "profile_id": f"P{index}", "profile_name": f"Profile {index}", "enabled": True,
            "launch_mt5": False, "mt5_folder": str(tmp_path / f"mt5-{index}"),
            "mt5_terminal": str(terminal), "broker": "XM", "server": "XMGlobal-MT5 5",
            "symbol": "GOLD#", "login_env": f"P{index}_LOGIN", "password_env": f"P{index}_PASSWORD",
            "runtime_directory": str(runtime), "database_path": str(runtime / "db.sqlite3"),
            "logs_directory": str(runtime / "logs"), "dashboard_path": str(runtime / "dashboard.html"),
            "learning_directory": str(runtime / "learning"), "knowledge_directory": str(runtime / "knowledge"),
            "statistics_directory": str(runtime / "statistics"), "execution": "LOCKED_SIMULATION_ONLY",
            "direct_execution": False, "live_execution": False,
        })
        monkeypatch.setenv(f"P{index}_LOGIN", str(1000 + index))
        monkeypatch.setenv(f"P{index}_PASSWORD", "secret")
        (runtime / "demo_execution_state.json").write_text(json.dumps({
            "status": "WAITING", "reason": "trading_cost_not_approved", "demo_verified": True,
            "armed": True, "order_status": "ORDER_NOT_SENT", "sent_units": 0,
            "decision_action": "BUY", "decision_confidence": 99.0,
            "execution": "DEMO_EXECUTION_ONLY", "checked_at_utc": "2999-01-01T00:00:00+00:00",
            "tickets": [],
        }), encoding="utf-8")
        (runtime / "mt5_health.json").write_text(json.dumps({
            "connection_status": "CONNECTED", "latency_ms": 5.0, "reconnect_attempts": 0,
            "reason": "ready", "checked_at_utc": "2999-01-01T00:00:00+00:00",
        }), encoding="utf-8")
    config.write_text(json.dumps({"profiles": profiles}), encoding="utf-8")
    html = DashboardUIRuntime().render_html({**default_dashboard_record(), "four_profile_config_path": str(config)})
    assert html.index("P1–P4 Live Operational Status") < html.index("Technical and certification panels")
    assert "trading_cost_not_approved" in html
    assert 'http-equiv="refresh" content="5"' in html


def test_supervisor_prefers_demo_runner_pid_and_exposes_freshness(tmp_path, monkeypatch):
    config = tmp_path / "profiles.json"
    runtime = tmp_path / "p1"; runtime.mkdir()
    terminal = tmp_path / "terminal.exe"; terminal.write_text("", encoding="utf-8")
    raw = {"profile_id":"P1","profile_name":"P1","enabled":True,"launch_mt5":False,
           "mt5_folder":str(tmp_path / "mt5"),"mt5_terminal":str(terminal),"broker":"XM",
           "server":"XMGlobal-MT5 5","symbol":"GOLD#","login_env":"P1_LOGIN","password_env":"P1_PASSWORD",
           "runtime_directory":str(runtime),"database_path":str(runtime / "db"),"logs_directory":str(runtime / "logs"),
           "dashboard_path":str(runtime / "dashboard"),"learning_directory":str(runtime / "learning"),
           "knowledge_directory":str(runtime / "knowledge"),"statistics_directory":str(runtime / "statistics")}
    config.write_text(json.dumps({"profiles":[raw]}), encoding="utf-8")
    monkeypatch.setenv("P1_LOGIN", "1001"); monkeypatch.setenv("P1_PASSWORD", "secret")
    (runtime / "demo_runner.pid").write_text("12345", encoding="utf-8")
    (runtime / "demo_execution_state.json").write_text(json.dumps({"status":"WAITING","checked_at_utc":"2999-01-01T00:00:00+00:00"}), encoding="utf-8")
    monkeypatch.setattr(FourProfileSupervisor, "_is_process_running", staticmethod(lambda pid: pid == 12345))
    row = FourProfileSupervisor(config).status().profiles[0]
    assert row["runtime_state"] == "RUNNING"
    assert row["runtime_kind"] == "DEMO_EXECUTION"
    assert row["data_fresh"] is True
