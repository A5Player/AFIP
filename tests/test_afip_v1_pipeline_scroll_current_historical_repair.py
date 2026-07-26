from afip.execution_pipeline_dashboard import render_execution_pipeline_dashboard
from afip.dashboard_ui.home import render_dashboard_home


def test_pipeline_has_no_meta_refresh_and_preserves_scroll():
    html = render_execution_pipeline_dashboard({"execution_pipelines": [], "generated_at_utc": "x"})
    assert '<meta http-equiv="refresh"' not in html
    assert "afip_pipeline_scroll" in html
    assert "padding:14px 14px 240px" in html
    assert "location.reload()" in html


def test_historical_stages_render_as_not_evaluated_current_state():
    contract = {
        "generated_at_utc": "x",
        "execution_pipelines": [{
            "profile_id": "P1", "profile_name": "Conservative", "data_status": "STALE",
            "data_age_seconds": 10, "evidence_mode": "HISTORICAL", "trace_id": "x",
            "overall_status": "HISTORICAL", "reason": "execution_evidence_stale",
            "current_stage": "execution_permission",
            "stages": [{"label": "Execution Permission", "status": "PASS", "detail": "ORDER_SENT"}],
        }],
    }
    html = render_execution_pipeline_dashboard(contract)
    assert "NOT_EVALUATED" in html
    assert "Last evidence: PASS · ORDER_SENT" in html


def test_command_center_iframe_explicitly_allows_scrolling():
    html = render_dashboard_home()
    assert 'scrolling="yes"' in html
    assert "overflow:auto" in html
