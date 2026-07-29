from pathlib import Path

from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime, _research_truth_summary
from afip.research_data_foundation.aggregator import ResearchDatasetAggregator


def test_empty_completed_samples_are_not_reported_as_zero_performance(tmp_path: Path) -> None:
    case_dir = tmp_path / "runtime" / "research" / "trade_cases"
    case_dir.mkdir(parents=True)
    (case_dir / "CASE-1.json").write_text(
        '{"trade_case_id":"CASE-1","data_lineage":{"source":"test"},"market_context":{"pattern_id":"P-A"},"lifecycle_state":"ACTIVE"}',
        encoding="utf-8",
    )
    row = ResearchDatasetAggregator(tmp_path / "runtime" / "research").build()["pattern_statistics"][0]
    assert row["statistics_status"] == "INSUFFICIENT_COMPLETED_TRADES"
    assert row["win_rate"] is None
    assert row["profit_factor"] is None
    assert row["maximum_drawdown"] is None


def test_completed_research_case_exposes_real_metrics(tmp_path: Path) -> None:
    case_dir = tmp_path / "runtime" / "research" / "trade_cases"
    case_dir.mkdir(parents=True)
    (case_dir / "CASE-1.json").write_text(
        '{"trade_case_id":"CASE-1","data_lineage":{"source":"test"},"market_context":{"pattern_id":"P-A"},"lifecycle_state":"CLOSED","exit_context":{"net_profit":5,"holding_seconds":60,"mfe":7,"mae":2,"exit_quality":80}}',
        encoding="utf-8",
    )
    row = ResearchDatasetAggregator(tmp_path / "runtime" / "research").build()["pattern_statistics"][0]
    assert row["statistics_status"] == "AVAILABLE"
    assert row["win_rate"] == 100.0
    assert row["net_profit"] == 5.0
    assert row["expectancy"] == 5.0


def test_research_truth_panel_is_honest_when_evidence_missing(tmp_path: Path) -> None:
    html, status = _research_truth_summary(tmp_path)
    assert status == "INSUFFICIENT_EVIDENCE"
    assert "DATA_UNAVAILABLE" in html
    assert "Zero is not presented as performance evidence" in html


def test_research_dashboard_contains_truth_and_connection_sections(tmp_path: Path) -> None:
    html = ThreeDashboardRuntime().render_research_html({}, tmp_path)
    assert "Research performance truth" in html
    assert "Research-to-trading connection audit" in html
    assert "SHOW TRUTH · NEVER INVENT METRICS" in html
    assert "Execution gate from research" in html
