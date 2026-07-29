import json
from pathlib import Path

from afip.control_center_runtime import ControlCenterRuntime
from afip.dashboard_ui.control_center import render_control_center


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_control_center_projects_existing_runtime_fields_without_placeholder_loss(tmp_path: Path) -> None:
    write(tmp_path / "runtime/dashboard/dashboard_monitor_status.json", {
        "status": "RUNNING", "updated_at_utc": "2026-07-28T03:14:55Z", "pid": 1234,
        "execution_authority": False, "order_send_called": False,
    })
    write(tmp_path / "runtime/final_integration_status.json", {
        "status": "RUNNING", "updated_at_utc": "2026-07-28T03:14:50Z",
        "trading_runtime": {"execution": "DEMO_EXECUTION_ONLY", "profiles": [{
            "profile_id": "P1", "runtime_state": "RUNNING", "gateway_status": "WAITING",
            "gateway_reason": "no_signal", "connected_account_login": "****0369",
        }]},
    })
    write(tmp_path / "runtime/research/automatic_research_status.json", {
        "status": "REVIEW", "reason": "research_dataset_already_current",
        "completed_at_utc": "2026-07-28T03:14:40Z",
        "replay_timeframe_evidence": {"M1": {"available_bars": 10, "covered_bars_after_run": 10, "bars_processed_this_run": 0, "coverage_complete": True}},
    })
    write(tmp_path / "runtime/research/research_engine_status.json", {
        "status": "RUNNING", "service_state": "RUNNING", "current_activity": "Research service waiting for next cycle",
        "updated_at_utc": "2026-07-28T03:14:45Z", "pid": 5678,
    })
    write(tmp_path / "runtime/dashboard/dashboard_runtime.json", {
        "profiles": [{"profile_id": "P1", "connection_status": "CONNECTED", "decision_action": "BUY", "decision_confidence": 99.0, "allocated_units": 1, "sent_units": 0}],
    })

    snapshot = ControlCenterRuntime(tmp_path).snapshot()
    assert snapshot["dashboard"]["process_state"] == "RUNNING"
    assert snapshot["dashboard"]["updated_at"] == "2026-07-28T03:14:55Z"
    assert snapshot["dashboard"]["pid"] == 1234
    assert snapshot["research"]["available_bars"] == 10
    assert snapshot["research"]["covered_bars"] == 10
    assert snapshot["research"]["progress_percent"] == 100.0
    assert snapshot["profiles"][0]["connection_status"] == "CONNECTED"
    assert snapshot["profiles"][0]["decision"] == "BUY"
    assert snapshot["profiles"][0]["login"] == "****0369"
    assert snapshot["startup"]["status"] == "NOT_RECORDED"

    html = render_control_center(tmp_path)
    assert "Dashboard Runtime" in html
    assert "Research service waiting for next cycle" in html
    assert "STARTUP_STATUS_NOT_GENERATED" in html
    assert "1234" in html


def test_control_center_remains_passive(tmp_path: Path) -> None:
    snapshot = ControlCenterRuntime(tmp_path).snapshot()
    assert snapshot["execution_authority_changed"] is False
    assert snapshot["execution_authority"] == "EXISTING_AFIP_RUNTIME_ONLY"
