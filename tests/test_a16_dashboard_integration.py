from afip.dashboard_ui.split_runtime import SplitDashboardRenderer


def test_a16_dashboard_renders_supplied_read_only_rankings(tmp_path):
    html = SplitDashboardRenderer().render_research_html({"a16_policy_rankings": [{
        "policy_id": "R_STEP", "sample_size": 30, "expectancy_after_cost_r": 0.5,
        "win_rate": 0.6, "average_mfe_r": 1.2, "average_mae_r": 0.4,
        "average_giveback_r": 0.2,
    }]}, tmp_path)
    assert "A16 Exit Path & R-ladder Research" in html
    assert "R_STEP" in html and "execution authority: NONE" in html


def test_a16_dashboard_never_invents_missing_rankings(tmp_path):
    html = SplitDashboardRenderer().render_research_html({}, tmp_path)
    assert "A16 exit-policy research has not reached its minimum sample yet" in html

def test_a16_dashboard_reads_append_only_ranking_dataset(tmp_path):
    path=tmp_path / "runtime" / "research" / "a16_exit_policy_rankings.jsonl"; path.parent.mkdir(parents=True)
    path.write_text('{"record":{"policy_id":"R_STEP","sample_size":30,"expectancy_after_cost_r":0.5,"win_rate":0.6,"average_mfe_r":1,"average_mae_r":0.4,"average_giveback_r":0.2,"research_rank":1}}\n', encoding="utf-8")
    assert "R_STEP" in SplitDashboardRenderer().render_research_html({}, tmp_path)
