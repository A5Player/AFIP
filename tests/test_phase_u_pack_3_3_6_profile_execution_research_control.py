from __future__ import annotations

import json
from pathlib import Path

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import FourProfileOperationalRuntime
from afip.timeframe_registry import get_timeframe_metadata, get_supported_timeframes


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "four_profile_demo.json"


class FailIfCalledMT5:
    def __getattr__(self, name):
        raise AssertionError(f"MT5 must not be called for execution-disabled profile: {name}")


def _raw_profiles():
    return json.loads(CONFIG.read_text(encoding="utf-8-sig"))["profiles"]


def test_operational_profile_requirement_is_explicit_and_reversible():
    rows = {row["profile_id"]: row for row in _raw_profiles()}
    assert {pid: rows[pid]["execution_enabled"] for pid in rows} == {
        "P1": True,
        "P2": True,
        "P3": True,
        "P4": True,
    }
    assert all(rows[pid]["enabled"] is True for pid in rows)
    assert all(rows[pid]["research_enabled"] is True for pid in rows)


def test_runtime_preserves_production_execution_and_reports_p4_research_only():
    runtime = FourProfileOperationalRuntime(CONFIG)
    profiles = {profile.profile_id: profile for profile in runtime.load()}
    assert profiles["P2"].capital_per_unit if hasattr(profiles["P2"], "capital_per_unit") else True
    records = {row["profile_id"]: row for row in runtime.prepare_isolation().profiles}
    assert records["P1"]["status"] == "READY"
    assert records["P2"]["status"] == "READY"
    assert records["P3"]["status"] == "READY"
    assert records["P4"]["status"] in {"READY", "BLOCKED"}
    assert records["P4"]["research_enabled"] is True
    assert "protected execution runtime" in records["P4"]["waiting_reason"].lower()


def test_p4_is_enabled_for_real_execution_with_fixed_single_unit():
    runtime = FourProfileOperationalRuntime(CONFIG)
    profiles = {profile.profile_id: profile for profile in runtime.load()}
    raw = {row["profile_id"]: row for row in _raw_profiles()}
    assert profiles["P4"].execution_enabled is True
    assert raw["P4"]["maximum_units"] == 1
    assert raw["P4"]["maximum_concurrent_orders"] == 1
    assert raw["P4"]["maximum_lot_per_order"] == 0.01

def test_research_collector_keeps_execution_disabled_profiles_eligible():
    profiles = FourProfileOperationalRuntime(CONFIG).load()
    eligible = {p.profile_id for p in profiles if p.enabled and p.research_enabled}
    assert eligible == {"P1", "P2", "P3", "P4"}


def test_m30_is_available_to_research_consumers_without_live_policy_change():
    assert get_supported_timeframes() == ("M1", "M5", "M15", "M30", "H1", "H4", "D1")
    metadata = get_timeframe_metadata("M30")
    assert metadata["research_enabled"] is True
    assert metadata["minutes"] == 30
    payload = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    assert payload["execution"] == "LOCKED_SIMULATION_ONLY"
    assert all(item["direct_execution"] is False for item in payload["profiles"])
    assert all(item["live_execution"] is False for item in payload["profiles"])
