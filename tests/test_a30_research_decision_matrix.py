import json
from pathlib import Path

from tools.afip_a30_research_decision_matrix import NA, build_report
from afip.dashboard_ui.split_runtime import SplitDashboardRenderer


def _write(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps({"record": item}) + "\n" for item in records), encoding="utf-8")


def test_matrix_keeps_exact_segments_separate_and_never_invents_performance(tmp_path):
    target = tmp_path / "runtime/research/automatic/schema_v2/adversarial_market_behaviour/outcomes.jsonl"
    _write(target, [
        {"pattern_name":"SWEEP", "timeframe":"H1", "threat_state":"TREND", "entry_policy":"WAIT", "forward_horizon_bars":8, "follow_through_direction":"UP", "upward_excursion_atr":2, "downward_excursion_atr":.5},
        {"pattern_name":"SWEEP", "timeframe":"M15", "threat_state":"TREND", "entry_policy":"WAIT", "forward_horizon_bars":4, "follow_through_direction":"DOWN", "upward_excursion_atr":.2, "downward_excursion_atr":1.5},
    ])
    report = build_report(tmp_path)
    assert report["row_count"] == 2
    assert {row["timeframe"] for row in report["rows"]} == {"H1", "M15"}
    assert all(row["win_rate"] == NA and row["max_drawdown"] == NA for row in report["rows"])


def test_matrix_is_profile_neutral_and_has_no_authority(tmp_path):
    report = build_report(tmp_path)
    assert report["profile_strategy_selection"] == "NOT_DECIDED"
    assert report["automatic_profile_assignment"] is False
    assert report["automatic_research_promotion"] is False
    assert report["execution_authority"] == "NONE" and report["orders_sent"] is False


def test_dashboard_renders_complete_trader_facing_columns(tmp_path):
    path = tmp_path / "runtime/research/a30_research_decision_matrix.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"row_count": 1, "profile_strategy_selection": "NOT_DECIDED",
        "execution_authority": "NONE", "ranking_method": "evidence only", "truth_notice": "truth",
        "rows": [{"evidence_order": 1, "pattern": "SWEEP", "timeframe": "H1", "samples": 30}]}), encoding="utf-8")
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    for text in ("A30 Research Decision Matrix", "Graph / pattern", "SL ATR±Buffer", "TP ATR±Buffer",
                 "Holding time", "Win rate", "Drawdown", "SWEEP", "NOT_DECIDED"):
        assert text in html
