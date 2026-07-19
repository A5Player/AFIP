import json
from pathlib import Path

from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _status() -> dict:
    timeframes = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")
    return {
        "status": "READY",
        "reason": "automatic_research_replay_updated",
        "schema_version": "AFIP-RESEARCH-SCHEMA-V2",
        "mt5_bars_collected": 14000,
        "replay_bars_processed": 14000,
        "replay_candidates_generated": 14000,
        "replay_completed": True,
        "historical_lake_appended": 14000,
        "historical_lake_duplicates": 0,
        "gap_ranges_detected": 1,
        "missing_bars_detected": 2,
        "freshness_review_timeframes": ["D1"],
        "backfill_ranges_requested": 1,
        "backfill_bars_returned": 2,
        "backfill_bars_accepted": 2,
        "live_execution_enabled": False,
        "order_send_called": False,
        "timeframe_data_quality": {
            tf: {
                "available_bars": 2000, "valid_bars": 2000, "gap_count": 0,
                "missing_bars": 0, "fresh": True, "integrity_status": "READY",
                "research_eligible": True,
            } for tf in timeframes
        },
        "replay_timeframe_evidence": {
            tf: {
                "available_bars": 2000, "bars_processed_this_run": 2000,
                "covered_bars_after_run": 2000, "coverage_complete": True,
            } for tf in timeframes
        },
    }


def test_dashboard_renders_all_registered_timeframes_and_m30(tmp_path: Path) -> None:
    status_path = tmp_path / "runtime" / "research" / "automatic_research_status.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text(json.dumps(_status()), encoding="utf-8")
    html = ThreeDashboardRuntime().render_research_html({}, tmp_path)
    for timeframe in ("M1", "M5", "M15", "M30", "H1", "H4", "D1"):
        assert f"<b>{timeframe}</b>" in html
    assert "Universal Timeframe Coverage" in html
    assert "Gaps / Missing" in html
    assert "Backfill accepted" in html
    assert "Live execution enabled</td><td>False" in html
    assert "Order send called</td><td>False" in html


def test_dashboard_missing_status_is_visible_and_deterministic(tmp_path: Path) -> None:
    html = ThreeDashboardRuntime().render_research_html({}, tmp_path)
    assert "DATA_UNAVAILABLE" in html
    assert html.count("<b>M30</b>") == 1
    assert "NOT_RECORDED" in html


def test_dashboard_write_keeps_three_page_backward_compatibility(tmp_path: Path) -> None:
    paths = ThreeDashboardRuntime().write_three_dashboards({}, tmp_path / "dashboard", tmp_path)
    assert len(paths) == 3
    assert all(path.exists() for path in paths)
    assert (tmp_path / "dashboard" / "afip_intelligence_research_dashboard.html").exists()
