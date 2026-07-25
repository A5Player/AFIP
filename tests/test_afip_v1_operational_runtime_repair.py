from __future__ import annotations
import json
from pathlib import Path
from afip.operational_runtime import OperationalRuntime, atomic_json, read_json

ROOT = Path(__file__).resolve().parents[1]


def test_atomic_json_utf8(tmp_path: Path) -> None:
    path = tmp_path / "runtime" / "authority.json"
    atomic_json(path, {"thai": "ข้อมูล", "status": "READY"})
    assert read_json(path)["thai"] == "ข้อมูล"
    assert not path.with_suffix(".json.tmp").exists()


def test_operational_snapshot_is_observability_only(tmp_path: Path, monkeypatch) -> None:
    runtime = OperationalRuntime(tmp_path)
    monkeypatch.setattr(runtime, "_router_status", lambda: {"router": {"running": True}, "profiles": [{"profile_id": "P1", "runtime_state": "RUNNING"}]})
    monkeypatch.setattr(runtime, "_research_status", lambda value: {"status": "READY", "heartbeat_stale": False, "collector": value})
    payload = runtime.snapshot({"status": "READY"}, {"status": "READY"})
    assert payload["status"] == "RUNNING"
    assert payload["execution_authority"] == "EXISTING_SEQUENTIAL_ROUTER_ONLY"
    assert payload["execution_authority_changed"] is False
    assert payload["order_send_authority_added"] is False


def test_stale_research_degrades_running_runtime(tmp_path: Path, monkeypatch) -> None:
    runtime = OperationalRuntime(tmp_path)
    monkeypatch.setattr(runtime, "_router_status", lambda: {"router": {"running": True}, "profiles": []})
    monkeypatch.setattr(runtime, "_research_status", lambda value: {"status": "STALE", "heartbeat_stale": True})
    assert runtime.snapshot()["status"] == "DEGRADED"


def test_operational_start_uses_single_lifecycle_authority():
    text = (ROOT / "tools" / "afip_operational_runtime.py").read_text(encoding="utf-8")
    start_block = text.split('if args.command == "start":', 1)[1].split('if args.command == "stop":', 1)[0]
    assert "runtime.start_background()" in start_block
    assert "afip_demo_execution_control" not in start_block
    assert '"lifecycle_authority": "OPERATIONAL_SUPERVISOR"' in start_block
    assert '"mt5_auto_launch": False' in start_block


def test_authority_separates_observability_from_execution():
    text = (ROOT / "afip" / "operational_runtime.py").read_text(encoding="utf-8")
    assert '"observability_running": True' in text
    assert '"execution_router_running": router_running' in text
