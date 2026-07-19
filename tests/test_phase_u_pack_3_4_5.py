from afip.research_dashboard import build_research_dashboard

def test_dashboard_contains_drawdown_and_status():
    html = build_research_dashboard({"top_overall": [{"research_id": "r1", "maximum_drawdown_percentage": 5, "evidence_status": "CERTIFIED"}]})
    assert "Maximum Drawdown %" in html
    assert "CERTIFIED" in html

def test_dashboard_escapes_values():
    html = build_research_dashboard({"top_overall": [{"research_id": "<script>"}]})
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

def test_dashboard_has_no_execution_permission():
    html = build_research_dashboard({})
    assert "Execution permission remains outside this dashboard" in html
