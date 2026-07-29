from pathlib import Path
from unittest.mock import Mock

from afip.final_integration.runtime import FinalIntegrationRuntime


def test_logical_service_treats_launcher_child_pair_as_one(tmp_path: Path, monkeypatch):
    runtime = FinalIntegrationRuntime(tmp_path)
    rows = [
        {"pid": 100, "parent_pid": 50, "command_line": f"{tmp_path} python -m tools.afip_dashboard_monitor --root {tmp_path}"},
        {"pid": 101, "parent_pid": 100, "command_line": f"{tmp_path} python -m tools.afip_dashboard_monitor --root {tmp_path}"},
    ]
    monkeypatch.setattr(runtime, "_process_inventory", lambda: rows)
    assert runtime._logical_service_pid("dashboard") == 100
    assert runtime._service_running("dashboard", runtime.dashboard_pid_path)
    assert runtime.dashboard_pid_path.read_text().strip() == "100"


def test_spawn_does_not_duplicate_existing_logical_service(tmp_path: Path, monkeypatch):
    runtime = FinalIntegrationRuntime(tmp_path)
    monkeypatch.setattr(runtime, "_service_running", lambda service, path=None: True)
    popen = Mock(side_effect=AssertionError("must not spawn duplicate"))
    monkeypatch.setattr("afip.final_integration.runtime.subprocess.Popen", popen)
    assert runtime._spawn("dashboard", runtime.dashboard_pid_path, ["python"], "x.log") is False
    popen.assert_not_called()


def test_service_detection_survives_missing_pid_file(tmp_path: Path, monkeypatch):
    runtime = FinalIntegrationRuntime(tmp_path)
    rows = [{"pid": 300, "parent_pid": 1, "command_line": f"{tmp_path} python -m tools.afip_final_integration research-forever --root {tmp_path}"}]
    monkeypatch.setattr(runtime, "_process_inventory", lambda: rows)
    assert not runtime.research_pid_path.exists()
    assert runtime._service_running("research", runtime.research_pid_path)
    assert runtime.research_pid_path.read_text().strip() == "300"


def test_terminate_service_targets_all_orphan_pair_pids(tmp_path: Path, monkeypatch):
    runtime = FinalIntegrationRuntime(tmp_path)
    rows = [
        {"pid": 400, "parent_pid": 99, "command_line": f"{tmp_path} python -m tools.afip_dashboard_monitor --root {tmp_path}"},
        {"pid": 401, "parent_pid": 400, "command_line": f"{tmp_path} python -m tools.afip_dashboard_monitor --root {tmp_path}"},
    ]
    monkeypatch.setattr(runtime, "_process_inventory", lambda: rows)
    monkeypatch.setattr("afip.final_integration.runtime.os.name", "nt")
    calls = []
    monkeypatch.setattr("afip.final_integration.runtime.subprocess.run", lambda args, **kwargs: calls.append(args))
    monkeypatch.setattr(runtime, "_terminate_pid", lambda path: None)
    runtime._terminate_service("dashboard", runtime.dashboard_pid_path)
    assert any("400" in call for call in calls)
    assert any("401" in call for call in calls)
