from __future__ import annotations

import json
from pathlib import Path

from afip.dashboard_data_contract import build_dashboard_contract
from afip.runtime_truth import build_profile_truth
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    root = tmp_path
    _write(root / "config/four_profile_demo.json", {
        "profiles": [{
            "profile_id": "P1", "profile_name": "Conservative", "enabled": True,
            "runtime_directory": "runtime/profiles/p1", "symbol": "GOLD#",
            "server": "XMGlobal-MT5 6", "sizing_authority": "CAPITAL_TIER_FORMULA_ONLY",
        }]
    })
    _write(root / "runtime/final_integration_status.json", {"trading_runtime": {"profiles": []}})
    _write(root / "runtime/execution/sequential_router_status.json", {"status": "RUNNING"})
    _write(root / "runtime/research/automatic_research_status.json", {"status": "RUNNING"})
    _write(root / "runtime/dashboard/dashboard_monitor_status.json", {"status": "RUNNING"})
    _write(root / "runtime/profiles/p1/mt5_health.json", {
        "profile_id": "P1", "process_alive": True, "monitoring_mode": "PASSIVE",
        "connection_status": "CONNECTED_PASSIVE", "evidence_kind": "PROCESS_ONLY",
    })
    _write(root / "runtime/profiles/p1/status.json", {"runtime_state": "RUNNING"})
    _write(root / "runtime/profiles/p1/demo_execution_state.json", {
        "account_balance": 0.0, "account_equity": 0.0, "status": "WAITING",
    })
    _write(root / "runtime/profiles/p1/mt5_live_snapshot.json", {
        "schema_version": "AFIP_PRO_LIVE_MT5_SNAPSHOT_V1",
        "profile_id": "P1", "process_alive": True,
        "monitoring_mode": "EXISTING_RUNTIME_SESSION_READ_ONLY",
        "connection_status": "CONNECTED", "evidence_kind": "LIVE",
        "snapshot_age_seconds": 0, "currency": "USD",
        "balance": 83.96, "equity": 83.96, "free_margin": 83.96,
        "margin": 0.0, "floating_profit": 0.0,
        "bid": 4049.07, "ask": 4049.31, "spread_points": 24.0,
        "positions_total": 0, "orders_total": 0,
        "execution_authority": False, "order_send_called": False,
    })
    return root


def test_live_snapshot_overrides_stale_execution_financial_aliases(tmp_path: Path) -> None:
    contract = build_dashboard_contract(_project(tmp_path))
    row = contract["profiles"][0]
    assert row["balance"] == 83.96
    assert row["account_balance"] == 83.96
    assert row["equity"] == 83.96
    assert row["account_equity"] == 83.96
    assert row["financial_state"] == "LIVE"
    assert row["financial_live"] is True
    assert row["financial_data_source"] == "AFIP_PRO_LIVE_MT5_SNAPSHOT_AUTHORITY"
    assert row["execution_authority"] is False
    assert row["order_send_called"] is False


def test_read_only_existing_session_live_evidence_is_live() -> None:
    truth = build_profile_truth({
        "enabled": True, "process_alive": True,
        "monitoring_mode": "EXISTING_RUNTIME_SESSION_READ_ONLY",
        "connection_status": "CONNECTED", "evidence_kind": "LIVE",
        "balance": 10.0, "snapshot_age_seconds": 0,
        "runtime_state": "RUNNING",
    })
    assert truth["financial_state"] == "LIVE"
    assert truth["financial_live"] is True


def test_summary_and_table_use_same_live_authority(tmp_path: Path) -> None:
    root = _project(tmp_path)
    contract = build_dashboard_contract(root)
    html = ThreeDashboardRuntime().render_profiles_html({"profiles": contract["profiles"], "project_root": str(root)})
    assert "Live financial" in html
    assert ">1/4<" in html
    assert ">83.96<" in html
    assert ">0.00<" in html
