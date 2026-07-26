import json
from pathlib import Path

from afip.dashboard_data_contract import SCHEMA_VERSION, build_dashboard_contract
from afip.dashboard_ui.authority_snapshot import enrich_profiles


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_contract_uses_real_runtime_sources_and_writes_atomically(tmp_path):
    _write(tmp_path / "config/four_profile_demo.json", {"profiles": [{"profile_id": "P1", "runtime_directory": "runtime/profiles/p1"}]})
    _write(tmp_path / "runtime/profiles/p1/mt5_health.json", {"profile_id": "P1", "balance": 123.45, "connection_status": "CONNECTED"})
    _write(tmp_path / "runtime/profiles/p1/status.json", {"runtime_state": "RUNNING"})
    snapshot = build_dashboard_contract(tmp_path)
    assert snapshot["schema_version"] == SCHEMA_VERSION
    assert snapshot["profiles"][0]["balance"] == 123.45
    assert snapshot["profiles"][0]["runtime_state"] == "RUNNING"
    assert snapshot["policy"]["dashboard_calculation_authority"] is False
    assert (tmp_path / "runtime/dashboard/dashboard_runtime.json").exists()
    assert not (tmp_path / "runtime/dashboard/dashboard_runtime.json.tmp").exists()


def test_contract_missing_values_are_not_invented(tmp_path):
    _write(tmp_path / "config/four_profile_demo.json", {"profiles": [{"profile_id": "P1"}]})
    snapshot = build_dashboard_contract(tmp_path)
    profile = snapshot["profiles"][0]
    assert "balance" not in profile
    assert profile["data_status"] == "DATA_UNAVAILABLE"
    assert snapshot["policy"]["missing_value_policy"] == "DATA_UNAVAILABLE"


def test_authority_snapshot_preserves_runtime_truth_over_supplied_display_defaults(tmp_path):
    _write(tmp_path / "config/four_profile_demo.json", {"profiles": [{"profile_id": "P1", "runtime_directory": "runtime/profiles/p1"}]})
    _write(tmp_path / "runtime/profiles/p1/mt5_health.json", {"balance": 500.0})
    rows = enrich_profiles([{"profile_id": "P1", "profile_name": "Safety"}], tmp_path)
    assert rows[0]["balance"] == 500.0
    assert rows[0]["profile_name"] == "Safety"
    assert rows[0]["dashboard_data_source"] == "AFIP_V1_DASHBOARD_DATA_CONTRACT"


def test_contract_is_read_only_for_execution(tmp_path):
    _write(tmp_path / "config/four_profile_demo.json", {"profiles": []})
    snapshot = build_dashboard_contract(tmp_path)
    assert snapshot["policy"]["trading_logic_changed"] is False
    assert snapshot["policy"]["mt5_initialization_allowed"] is False
    assert snapshot["policy"]["order_send_allowed"] is False
