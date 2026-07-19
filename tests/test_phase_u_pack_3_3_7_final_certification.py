from __future__ import annotations

import json
from pathlib import Path

from afip.four_profile_operations.runtime import FourProfileOperationalRuntime
from afip.timeframe_registry import get_supported_timeframes, get_timeframe_metadata

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "four_profile_demo.json"
EXPECTED = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def test_pack_3_3_timeframe_scope_is_complete_and_ordered():
    assert get_supported_timeframes() == EXPECTED
    assert get_timeframe_metadata("M30")["minutes"] == 30
    assert get_timeframe_metadata("M30")["research_enabled"] is True


def test_pack_3_3_required_modules_exist():
    required = (
        "afip/timeframe_registry.py",
        "afip/historical_data_manager/download_pipeline.py",
        "afip/historical_data_manager/timeframe_quality.py",
        "afip/automatic_research_runtime/runtime.py",
        "afip/financial_data_lake/runtime.py",
        "afip/dashboard_ui/split_runtime.py",
        "afip/four_profile_operations/runtime.py",
        "afip/demo_execution_gateway/runtime.py",
    )
    assert all((ROOT / path).is_file() for path in required)


def test_pack_3_3_regression_tests_are_present():
    expected_tests = tuple(
        ROOT / "tests" / f"test_phase_u_pack_3_3_{suffix}.py"
        for suffix in (
            "1_timeframe_registry",
            "2_m30_historical_data_lake",
            "3_m30_replay_coverage",
            "4_m30_quality_backfill",
            "5_dashboard_timeframe_status",
            "6_profile_execution_research_control",
        )
    )
    assert all(path.is_file() for path in expected_tests)


def test_profile_execution_control_matches_operational_requirement():
    payload = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    profiles = {row["profile_id"]: row for row in payload["profiles"]}
    assert {pid: profiles[pid]["execution_enabled"] for pid in profiles} == {
        "P1": True,
        "P2": True,
        "P3": True,
        "P4": False,
    }
    assert all(profiles[pid]["enabled"] is True for pid in profiles)
    assert all(profiles[pid]["research_enabled"] is True for pid in profiles)


def test_p4_is_research_only_without_configuration_removal():
    runtime = FourProfileOperationalRuntime(CONFIG)
    loaded = {item.profile_id: item for item in runtime.load()}
    records = {row["profile_id"]: row for row in runtime.prepare_isolation().profiles}
    for pid in ("P4",):
        assert pid in loaded
        assert records[pid]["status"] == "RESEARCH_ONLY"
        assert records[pid]["execution_enabled"] is False
        assert records[pid]["research_enabled"] is True


def test_live_execution_remains_locked_and_no_martingale_is_preserved():
    payload = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    assert payload["execution"] == "LOCKED_SIMULATION_ONLY"
    assert payload["position_policy"]["martingale_allowed"] is False
    assert all(row["direct_execution"] is False for row in payload["profiles"])
    assert all(row["live_execution"] is False for row in payload["profiles"])


def test_pack_3_3_documentation_and_runners_are_complete():
    required = (
        "README_PHASE_U_PACK_3_3_7.md",
        "README_PHASE_U_PACK_3_3_7_TH.md",
        "FILE_LIST_PHASE_U_PACK_3_3_7.md",
        "RUN_PHASE_U_PACK_3_3_7.ps1",
        "RUN_PHASE_U_PACK_3_3_7.bat",
        "APPLY_PHASE_U_PACK_3_3_7_DOC_UPDATES.ps1",
        "AFIP_PROJECT_DATABASE_PHASE_U_PACK_3_3_7_APPEND.md",
        "HANDOFF_PHASE_U_PACK_3_3_7_APPEND.md",
    )
    assert all((ROOT / path).is_file() for path in required)
