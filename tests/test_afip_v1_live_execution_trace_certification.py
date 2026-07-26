from __future__ import annotations

import json
from pathlib import Path

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import ProfileOperationalConfig


def _profile(tmp_path: Path) -> ProfileOperationalConfig:
    terminal = tmp_path / "terminal64.exe"
    terminal.write_text("", encoding="utf-8")
    return ProfileOperationalConfig(
        profile_id="P1", profile_name="High Safety", enabled=True, launch_mt5=False,
        mt5_folder=tmp_path, mt5_terminal=terminal, broker="XM", server="XMGlobal-MT5 6",
        symbol="GOLD#", login_env="AFIP_P1_LOGIN", password_env="AFIP_P1_PASSWORD",
        runtime_directory=tmp_path / "runtime", database_path=tmp_path / "database" / "afip.sqlite3",
        logs_directory=tmp_path / "logs", dashboard_path=tmp_path / "dashboard" / "index.html",
        learning_directory=tmp_path / "learning", knowledge_directory=tmp_path / "knowledge",
        statistics_directory=tmp_path / "statistics",
    )


def _policy() -> DemoProfilePolicy:
    return DemoProfilePolicy.from_mapping({
        "profile_id": "P1", "enabled": True, "execution_enabled": True,
        "demo_execution_enabled": True, "maximum_units": 3,
        "minimum_confidence": 98, "minimum_seconds_between_entries": 900,
        "magic": 26071001, "lot_per_unit": 0.01,
        "allocation_mode": "CAPITAL_TIER_TABLE", "maximum_concurrent_orders": 3,
        "maximum_lot_per_order": 0.01,
        "capital_tiers": [{"minimum_balance": 0, "lots": [0.01, 0.01, 0.01]}],
    })


class NeverReachedMT5:
    pass


def test_blocked_cycle_persists_trace_identity_and_reason_chain(tmp_path, monkeypatch):
    monkeypatch.delenv("AFIP_DEMO_EXECUTION_ARMED", raising=False)
    monkeypatch.delenv("AFIP_P1_DEMO_ARMED", raising=False)
    gateway = DemoExecutionGateway(_profile(tmp_path), _policy(), mt5=NeverReachedMT5())

    report = gateway.run_cycle()

    assert report.status == "BLOCKED"
    assert report.reason == "local_demo_execution_not_armed"
    assert report.execution_trace_id.startswith("AFIP-P1-")
    assert report.trace_stage == "PREFLIGHT"
    assert report.reason_chain == ("PREFLIGHT", "BLOCKED", "local_demo_execution_not_armed")

    state = json.loads(gateway.state_path.read_text(encoding="utf-8"))
    assert state["execution_trace_id"] == report.execution_trace_id
    assert state["reason_chain"] == list(report.reason_chain)


def test_authority_snapshot_records_actual_decision_and_sizing_fields(tmp_path):
    gateway = DemoExecutionGateway(_profile(tmp_path), _policy(), mt5=NeverReachedMT5())

    report = gateway._report(
        "WAITING", "profile_order_capacity_unavailable",
        decision_action="BUY", decision_confidence=99.5,
        approved_units=2, approved_lots=(0.01, 0.01),
        total_approved_lot=0.02, limiting_gate="CAPITAL_UNITS",
        sizing_reason="capital_tier_capacity", remaining_order_capacity=0,
    )

    assert report.trace_stage == "LOT_CAPITAL_AUTHORITY"
    assert report.authority_snapshot["decision_action"] == "BUY"
    assert report.authority_snapshot["approved_units"] == 2
    assert report.authority_snapshot["approved_lots"] == (0.01, 0.01)
    assert report.authority_snapshot["limiting_gate"] == "CAPITAL_UNITS"
