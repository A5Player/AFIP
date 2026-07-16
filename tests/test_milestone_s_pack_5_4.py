from __future__ import annotations

import json
from pathlib import Path

from afip.dashboard_ui.runtime import DashboardUIRuntime
from afip.research_data_foundation import ResearchDashboardSnapshot, ResearchDatasetAggregator


def _case(root: Path, case_id: str, *, state: str, pattern: str, profit: float | None) -> None:
    exit_context = {} if profit is None else {
        "net_profit": profit,
        "holding_seconds": 900,
        "mfe": 12.0,
        "mae": -4.0,
        "exit_quality": 80.0,
    }
    payload = {
        "trade_case_id": case_id,
        "lifecycle_state": state,
        "market_context": {"pattern_id": pattern},
        "exit_context": exit_context,
        "data_lineage": {"source_event_id": f"EVT-{case_id}"},
        "post_trade_checkpoints": {
            name: {"status": "COMPLETED" if state == "COMPLETE" else "PENDING"}
            for name in ("M15", "M30", "H1", "H4", "D1")
        },
    }
    target = root / "trade_cases" / f"{case_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload), encoding="utf-8")


def test_research_aggregator_builds_health_lifecycle_and_pattern_statistics(tmp_path: Path) -> None:
    _case(tmp_path, "CASE-A", state="COMPLETE", pattern="PATTERN-A", profit=10.0)
    _case(tmp_path, "CASE-B", state="OPEN_OR_SUBMITTED", pattern="PATTERN-A", profit=None)
    _case(tmp_path, "CASE-C", state="CLOSED_POST_TRADE_OBSERVATION_PENDING", pattern="UNKNOWN", profit=-5.0)

    result = ResearchDatasetAggregator(tmp_path).build()

    assert result["research_only"] is True
    assert result["affects_trading"] is False
    assert result["dataset_health"]["status"] == "READY"
    assert result["dataset_health"]["trade_case_count"] == 3
    assert result["dataset_health"]["active_lifecycle_count"] == 1
    assert result["dataset_health"]["closed_case_count"] == 2
    assert result["pending_checkpoints"]["M15"] == 2
    assert result["top_100_patterns"][0]["pattern_id"] == "PATTERN-A"


def test_dashboard_snapshot_exposes_real_time_research_projection(tmp_path: Path) -> None:
    _case(tmp_path, "CASE-A", state="OPEN_OR_SUBMITTED", pattern="PATTERN-A", profit=None)

    snapshot = ResearchDashboardSnapshot(tmp_path).build()

    assert snapshot["dataset_health"]["active_lifecycle_count"] == 1
    assert snapshot["pending_checkpoints"] == {"M15": 1, "M30": 1, "H1": 1, "H4": 1, "D1": 1}
    assert snapshot["top_100_patterns"][0]["affects_trading"] is False


def test_dashboard_panel_is_permanent_and_research_only(tmp_path: Path) -> None:
    _case(tmp_path, "CASE-A", state="OPEN_OR_SUBMITTED", pattern="PATTERN-A", profit=None)
    report = DashboardUIRuntime().evaluate_one({"research_root": str(tmp_path)})
    panel = next(panel for panel in report.panels if panel.panel_id == "research_foundation")
    rows = dict(panel.rows)

    assert rows["Dataset Health"] == "READY"
    assert rows["Active Lifecycle"] == "1"
    assert rows["Research Only"] == "True"
    assert rows["Affects Trading"] == "False"
