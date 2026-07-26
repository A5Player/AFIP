from afip.execution_pipeline_dashboard import render_execution_pipeline_dashboard
from afip.live_mt5_dashboard import render


def test_pipeline_preserves_scroll_and_has_four_columns():
    html = render_execution_pipeline_dashboard({"execution_pipelines": [], "generated_at_utc": "x"})
    assert "repeat(4,minmax(0,1fr))" in html
    assert "afip_pipeline_scroll" in html


def test_live_mt5_four_columns_and_complete_fields():
    html = render({"profiles": [{"profile_id": "P1", "account": "****1", "checked_at_utc": "2026-01-01T00:00:00Z"}]})
    assert "repeat(4,minmax(0,1fr))" in html
    assert "****1" in html
    assert "Bid / Ask" in html
    assert "Positions / Orders" in html
    assert "afip_mt5_scroll" in html
