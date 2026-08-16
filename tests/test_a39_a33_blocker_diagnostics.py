import json
from pathlib import Path

from afip.final_integration.continuous_research import ContinuousResearchPipeline
from tools.afip_a39_a33_blocker_diagnostics import SOURCE, build_report, write_outputs


def _row(**updates):
    value = {
        "rank": 1, "timeframe": "M5", "pattern": "SIDEWAY_COMPRESSION", "direction": "BUY",
        "tp_points": 1200, "sl_points": 500, "samples": 138, "win_rate_pct": 45.65,
        "expectancy_r": .176, "profit_factor": 1.44, "max_drawdown_r": 8.3,
        "walk_forward_passes": 1, "walk_forward_windows": 4, "planned_rr": 2.4,
        "minimum_win_rate_for_rr_pct": 42, "metric_gate_pass": True,
        "eligibility": "NOT_ELIGIBLE", "eligibility_reasons": ["WALK_FORWARD_BELOW_3_OF_4"],
    }
    value.update(updates)
    return value


def _write_a33(root: Path, rows):
    path = root / SOURCE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"rankings": {"balanced": rows}}), encoding="utf-8")


def test_a39_counts_blockers_without_changing_thresholds(tmp_path: Path):
    _write_a33(tmp_path, [_row(), _row(rank=2, metric_gate_pass=False,
        eligibility_reasons=["NET_EXPECTANCY_BELOW_0_15R", "WALK_FORWARD_BELOW_3_OF_4"])])
    report = build_report(tmp_path)
    assert report["status"] == "A33_RESEARCH_ELIGIBILITY_BLOCKED"
    assert report["summary"] == {"balanced_rows": 2, "metric_gate_pass_rows": 1,
                                  "walk_forward_3_of_4_rows": 0, "eligible_rows": 0}
    assert report["blocker_counts"][0] == {"reason": "WALK_FORWARD_BELOW_3_OF_4", "rows": 2}
    assert report["threshold_change_authorized"] is False


def test_a39_never_grants_execution_authority(tmp_path: Path):
    _write_a33(tmp_path, [_row(eligibility="ELIGIBLE", eligibility_reasons=[],
                                    walk_forward_passes=3)])
    report = build_report(tmp_path)
    assert report["status"] == "ELIGIBLE_ROWS_AVAILABLE_FOR_MANUAL_REVIEW"
    assert report["profile_strategy_selection"] == "NOT_DECIDED"
    assert report["automatic_profile_assignment"] is False
    assert report["demo_order_authorized"] is False
    assert report["live_order_authorized"] is False
    assert report["execution_authority"] == "NONE"
    assert report["orders_sent"] is False


def test_a39_writes_readable_outputs(tmp_path: Path):
    _write_a33(tmp_path, [_row()])
    report = build_report(tmp_path)
    json_path, html_path = write_outputs(report, tmp_path)
    assert json.loads(json_path.read_text())["status"] == report["status"]
    html = html_path.read_text(encoding="utf-8")
    assert "A39 A33 Eligibility Blocker Diagnostics" in html
    assert "Threshold" not in html or "never changes thresholds" in html
    assert "Execution authority NONE" in html


def test_a39_source_has_no_mt5_or_order_authority():
    source = Path(__file__).resolve().parents[1] / "tools/afip_a39_a33_blocker_diagnostics.py"
    text = source.read_text(encoding="utf-8")
    assert "MetaTrader5" not in text
    assert ".order_send(" not in text
    assert ".order_check(" not in text


def test_a37_runs_a39_only_when_a33_changes(tmp_path: Path):
    _write_a33(tmp_path, [_row()])
    pipeline = ContinuousResearchPipeline(tmp_path)
    first = pipeline.run_once()
    second = pipeline.run_once()
    assert "A39_A33_BLOCKER_DIAGNOSTICS" in {item["stage"] for item in first["stages"]}
    assert "A39_A33_BLOCKER_DIAGNOSTICS" not in {item["stage"] for item in second["stages"]}


def test_dashboard_renders_a39_blockers(tmp_path: Path):
    from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
    _write_a33(tmp_path, [_row()])
    report = build_report(tmp_path)
    write_outputs(report, tmp_path)
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "A39 A33 Eligibility Blocker Diagnostics" in html
    assert "WALK_FORWARD_BELOW_3_OF_4" in html
    assert "Threshold change false" in html
