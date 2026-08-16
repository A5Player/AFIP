import json
from pathlib import Path

from afip.final_integration.continuous_research import ContinuousResearchPipeline
from tools.afip_a38_research_readiness_gate import REPORTS, build_report, write_outputs


def _write(root: Path, name: str, value: dict) -> None:
    path = root / REPORTS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _passing_evidence(root: Path) -> None:
    candidate = {
        "rank": 1, "pattern": "SAFE_PATTERN", "timeframe": "H1", "direction": "BUY",
        "samples": 120, "win_rate_pct": 64.0, "expectancy_r": .25, "profit_factor": 1.6,
        "max_drawdown_r": 7.0, "sl_points": 500, "tp_points": 750,
        "walk_forward_passes": 3, "walk_forward_windows": 4,
        "eligibility": "ELIGIBLE_RESEARCH",
    }
    _write(root, "A32", {"rows": [candidate]})
    _write(root, "A33", {"rankings": {"balanced": [candidate]}, "eligible_rows": 1})
    _write(root, "A35", {"rows": [candidate], "eligible_research_rows": 1})
    _write(root, "A36", {"candidate_count": 1, "eligible_research_candidates": [candidate]})
    _write(root, "A37", {"status": "READY"})


def test_missing_reports_fail_closed_without_authority(tmp_path: Path):
    report = build_report(tmp_path)
    assert report["status"] == "BLOCKED_RESEARCH_EVIDENCE_INCOMPLETE"
    assert report["missing_reports"]
    assert report["demo_order_authorized"] is False
    assert report["live_order_authorized"] is False
    assert report["execution_authority"] == "NONE"
    assert report["profile_strategy_selection"] == "NOT_DECIDED"
    assert report["automatic_profile_assignment"] is False


def test_passing_research_requires_manual_separate_demo_approval(tmp_path: Path):
    _passing_evidence(tmp_path)
    report = build_report(tmp_path)
    assert report["status"] == "READY_FOR_MANUAL_DEMO_REVIEW"
    assert report["blocking_reasons"] == []
    assert report["next_required_action"] == "MANUAL_REVIEW_AND_SEPARATE_BOUNDED_DEMO_APPROVAL"
    assert report["demo_order_authorized"] is False
    assert report["live_order_authorized"] is False
    assert report["orders_sent"] is False


def test_a38_writes_json_and_standalone_html(tmp_path: Path):
    report = build_report(tmp_path)
    json_path, html_path = write_outputs(report, tmp_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == report["status"]
    html = html_path.read_text(encoding="utf-8")
    assert "A38 Research Readiness &amp; Demo Eligibility" in html
    assert "Execution authority: NONE" in html
    assert "distances from entry" in html
    assert report["point_definition"] == "1 point = 0.01 GOLD# price distance"


def test_candidate_separates_points_from_absolute_gold_price(tmp_path: Path):
    _passing_evidence(tmp_path)
    report = build_report(tmp_path)
    candidate = report["candidates"][0]
    assert candidate["sl_distance_points"] == 500
    assert candidate["sl_price_distance"] == 5.0
    assert candidate["tp_distance_points"] == 750
    assert candidate["tp_price_distance"] == 7.5
    assert "sl_points" not in candidate


def test_a38_source_has_no_mt5_or_order_calls():
    source = Path(__file__).resolve().parents[1] / "tools/afip_a38_research_readiness_gate.py"
    text = source.read_text(encoding="utf-8")
    assert "MetaTrader5" not in text
    assert ".order_check(" not in text
    assert ".order_send(" not in text
    for prohibited in ("DEMO_AUTHORIZED", "LIVE_AUTHORIZED", "PRODUCTION_READY", "REAL_MONEY_READY"):
        assert prohibited not in text


def test_a37_runs_a38_only_after_input_change(tmp_path: Path):
    _passing_evidence(tmp_path)
    pipeline = ContinuousResearchPipeline(tmp_path)
    first = pipeline.run_once()
    second = pipeline.run_once()
    assert "A38_RESEARCH_READINESS" in {item["stage"] for item in first["stages"]}
    assert "A38_RESEARCH_READINESS" not in {item["stage"] for item in second["stages"]}
    assert second["cycle_result"] == "NO_NEW_EVIDENCE"


def test_dashboard_renders_a38_readiness_and_blockers(tmp_path: Path):
    from afip.dashboard_ui.split_runtime import SplitDashboardRenderer
    report = build_report(tmp_path)
    write_outputs(report, tmp_path)
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "A38 Research Readiness &amp; Demo Eligibility" in html
    assert "A33_NO_ELIGIBLE_BALANCED_ROWS" in html
    assert "Demo authorized: false" in html
