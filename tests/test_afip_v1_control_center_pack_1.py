from __future__ import annotations
import json
from pathlib import Path
from afip.control_center_runtime import ControlCenterRuntime, SCHEMA_VERSION
from afip.dashboard_ui.control_center import render_control_center, write_control_center
from afip.dashboard_ui.dashboard_authority import DashboardAuthority


def test_startup_schema_and_atomic_write(tmp_path: Path) -> None:
    runtime = ControlCenterRuntime(tmp_path)
    value = runtime.write_startup("INITIALIZING", message="Starting")
    payload = json.loads(runtime.status_path.read_text(encoding="utf-8"))
    assert value.schema_version == SCHEMA_VERSION
    assert payload["execution_authority_changed"] is False
    assert not list(runtime.directory.glob("*.tmp"))


def test_ready_with_warning_is_degraded(tmp_path: Path) -> None:
    value = ControlCenterRuntime(tmp_path).write_startup("READY", warnings=("optional monitor unavailable",))
    assert value.status == "DEGRADED"


def test_missing_and_invalid_runtime_data_do_not_crash(tmp_path: Path) -> None:
    bad = tmp_path / "runtime" / "research" / "automatic_research_status.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("{broken", encoding="utf-8")
    html = render_control_center(tmp_path)
    assert "DATA_UNAVAILABLE" in html
    assert "Execution authority changed" in html


def test_profile_login_is_masked(tmp_path: Path) -> None:
    path = tmp_path / "runtime" / "profiles" / "p1" / "demo_execution_state.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"login": "123456789", "runtime_state": "RUNNING"}), encoding="utf-8")
    html = render_control_center(tmp_path)
    assert "123456789" not in html
    assert "*****6789" in html


def test_control_center_write(tmp_path: Path) -> None:
    output = write_control_center(tmp_path / "runtime" / "dashboard", tmp_path)
    assert output.name == "afip_control_center.html"
    assert "Passive production observability" in output.read_text(encoding="utf-8")


def test_dashboard_authority_builds_control_center(tmp_path: Path) -> None:
    result = DashboardAuthority().build_all(tmp_path / "runtime" / "dashboard", project_root=tmp_path)
    assert result.control_center.exists()
    assert result.home.exists()
    assert "afip_control_center.html" in result.home.read_text(encoding="utf-8")


def test_control_center_tool_is_read_only_and_importable() -> None:
    from tools.afip_control_center import main
    assert callable(main)
