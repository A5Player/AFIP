from __future__ import annotations

import json
from pathlib import Path

from afip.research_data_foundation.aggregator import ResearchDatasetAggregator
from afip.research_data_foundation.dashboard import ResearchDashboardSnapshot


def _write_case(root: Path, case_id: str, *, pattern: str, status: str, net: float, regime: str = "TREND") -> None:
    path = root / "trade_cases" / f"{case_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "trade_case_id": case_id,
        "data_lineage": {"source": "test"},
        "lifecycle_state": "CLOSED",
        "market_context": {"pattern_id": pattern, "market_regime": regime},
        "exit_context": {
            "research_feedback_status": status,
            "net_realized_profit_usd": net,
            "gross_realized_profit_usd": net,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_pattern_statistics_use_only_eligible_net_after_costs(tmp_path: Path) -> None:
    _write_case(tmp_path, "CASE-1", pattern="PAT-A", status="ELIGIBLE", net=10.0)
    _write_case(tmp_path, "CASE-2", pattern="PAT-A", status="QUARANTINED", net=1000.0)
    result = ResearchDatasetAggregator(tmp_path).build()
    row = result["pattern_statistics"][0]
    assert row["completed_trades"] == 1
    assert row["net_profit"] == 10.0
    assert row["eligible_feedback_count"] == 1
    assert row["quarantined_feedback_count"] == 1


def test_ranking_not_ready_below_minimum_sample(tmp_path: Path) -> None:
    for i in range(29):
        _write_case(tmp_path, f"CASE-{i}", pattern="PAT-A", status="ELIGIBLE", net=1.0)
    result = ResearchDatasetAggregator(tmp_path).build()
    assert result["ranking_readiness"]["status"] == "NOT_READY_FOR_AUTOMATIC_RANKING"
    assert result["dataset_health"]["sample_ready_pattern_count"] == 0


def test_ranking_ready_at_30_clean_eligible_samples(tmp_path: Path) -> None:
    for i in range(30):
        _write_case(tmp_path, f"CASE-{i}", pattern="PAT-A", status="ELIGIBLE", net=1.0)
    result = ResearchDatasetAggregator(tmp_path).build()
    assert result["ranking_readiness"]["status"] == "READY_FOR_RESEARCH_RANKING"
    assert result["dataset_health"]["sample_ready_pattern_count"] == 1
    assert result["dataset_health"]["certification_blockers"] == []


def test_unknown_pattern_blocks_ranking(tmp_path: Path) -> None:
    for i in range(30):
        _write_case(tmp_path, f"CASE-{i}", pattern="PAT-A", status="ELIGIBLE", net=1.0)
    _write_case(tmp_path, "CASE-UNKNOWN", pattern="UNKNOWN", status="ELIGIBLE", net=1.0)
    result = ResearchDatasetAggregator(tmp_path).build()
    assert "unknown_pattern_cases" in result["dataset_health"]["certification_blockers"]
    assert result["ranking_readiness"]["status"] == "NOT_READY_FOR_AUTOMATIC_RANKING"


def test_dashboard_exposes_ranking_readiness(tmp_path: Path) -> None:
    for i in range(30):
        _write_case(tmp_path, f"CASE-{i}", pattern="PAT-A", status="ELIGIBLE", net=1.0)
    snapshot = ResearchDashboardSnapshot(tmp_path).build()
    assert snapshot["ranking_readiness"]["eligible_feedback_only"] is True
    assert snapshot["ranking_readiness"]["uses_net_realized_profit_after_costs"] is True
    assert snapshot["ranking_readiness"]["automatic_ranking_mutation"] is False
