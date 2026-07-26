from pathlib import Path

from afip.dashboard_ui.home import render_dashboard_home
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime
from afip.order_evidence_dashboard import render_order_evidence_dashboard
from afip.research_observability_dashboard import render as render_observability


def test_operations_running_badge_uses_runtime_state_color():
    html = ThreeDashboardRuntime().render_profiles_html({})
    assert '_runtime_state_class' not in html
    assert 'status-pill ready' in html or 'status-pill stopped' in html


def test_order_evidence_is_fixed_four_column_layout():
    html = render_order_evidence_dashboard({"profiles": [], "order_evidence": []})
    assert 'grid-template-columns:repeat(4,minmax(0,1fr))' in html


def test_home_removes_unified_and_combines_observability_audit():
    html = render_dashboard_home()
    assert 'data-page="unified"' not in html
    assert 'data-page="audit"' not in html
    assert 'Research Observability &amp; Audit' in html


def test_research_status_and_timeframe_are_side_by_side_and_rankings_four_column():
    html = ThreeDashboardRuntime().render_research_html({}, project_root='.')
    assert 'research-status-layout' in html
    assert 'grid-template-columns:minmax(300px,.72fr) minmax(0,2.28fr)' in html
    assert 'grid-template-columns:repeat(4,minmax(0,1fr))' in html


def test_combined_observability_contains_research_and_audit():
    html = render_observability({"research": {"status": "READY"}, "sources": {}})
    assert 'Research Observability' in html
    assert 'Dashboard Source Audit' in html


def test_all_primary_pages_have_bottom_safety_space():
    root = Path('runtime/dashboard')
    for name in (
        'afip_profiles_dashboard.html',
        'afip_intelligence_engine_dashboard.html',
        'afip_order_evidence_dashboard.html',
        'afip_live_mt5_dashboard.html',
        'afip_research_data_dashboard.html',
    ):
        text = (root / name).read_text(encoding='utf-8')
        assert '100px' in text or '110px' in text or 'padding-bottom:96px' in text
