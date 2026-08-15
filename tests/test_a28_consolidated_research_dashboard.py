import json
from pathlib import Path

from afip.dashboard_ui.split_runtime import SplitDashboardRenderer


def _write(root: Path, dataset: str, records: list[dict]) -> None:
    path = root / "runtime" / "research"
    path.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"record_sequence": index, "chain_checksum": f"C{index}", "record": record})
             for index, record in enumerate(records, 1)]
    (path / f"{dataset}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_append_only_envelopes_are_unwrapped_for_real_performance_ranking(tmp_path: Path):
    _write(tmp_path, "pattern_outcomes", [
        {"pattern_name": "REAL_PATTERN_X", "outcome": "WIN", "realized_profit": 2.5},
        {"pattern_name": "REAL_PATTERN_X", "outcome": "LOSS", "realized_profit": -1.0},
    ])
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "REAL_PATTERN_X" in html
    assert "2</td><td>1</td><td>1" in html
    assert "1.50" in html


def test_all_research_is_grouped_into_explicit_categories(tmp_path: Path):
    _write(tmp_path, "historical_data_quality", [{"status": "PASS"}])
    _write(tmp_path, "a24_tp_volume_decisions", [{"recommended_action": "EXIT_WATCH"}])
    _write(tmp_path, "initial_capital_pattern_observations", [{"pattern_id": "CAP-1"}])
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "All Research · Category Overview" in html
    assert "DATA, REPLAY &amp; QUALITY" in html
    assert "EXIT, HOLDING &amp; TP" in html
    assert "CAPITAL, RISK &amp; PROFIT" in html
    assert "a24_tp_volume_decisions" in html


def test_persisted_rank_is_displayed_without_dashboard_promotion_authority(tmp_path: Path):
    _write(tmp_path, "a16_exit_policy_rankings", [{
        "research_rank": 1, "policy_id": "R_STEP", "sample_size": 40,
        "expectancy_after_cost_r": 0.31, "status": "RESEARCH_ONLY",
    }])
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "Recorded Rankings Across All Categories" in html
    assert "R_STEP" in html and "0.31" in html
    assert "dashboard does not calculate promotion authority" in html
    assert "Execution gate from research: RESEARCH_ONLY" in html


def test_inventory_counts_outcomes_and_ranked_records_separately(tmp_path: Path):
    _write(tmp_path, "a22_holding_exit_validation_results", [
        {"result_id": "A22-1", "research_rank": 2, "net_realized_r": 0.4},
        {"result_id": "A22-2", "status": "WAIT"},
    ])
    records, counts = SplitDashboardRenderer()._load_research_records(tmp_path)
    catalogue = SplitDashboardRenderer()._research_catalogue(records)
    item = next(value for value in catalogue if value["dataset"] == "a22_holding_exit_validation_results")
    assert counts["records"] == 2
    assert item["records"] == 2 and item["outcomes"] == 1 and item["ranked"] == 1
    assert item["chained"] == 2
