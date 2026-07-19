from afip.dashboard_ui.split_runtime import SplitDashboardRenderer


def test_dashboard_2_uses_compact_equal_height_grid():
    html = SplitDashboardRenderer().render_intelligence_html({})
    assert 'class="intelligence-grid"' in html
    assert 'height:360px' in html
    assert 'white-space:nowrap' in html
    assert 'text-overflow:ellipsis' in html
    assert 'class="table-wrap"' in html


def test_dashboard_2_keeps_manual_refresh_and_links():
    html = SplitDashboardRenderer().render_intelligence_html({})
    assert 'window.location.reload()' in html
    assert 'afip_profiles_dashboard.html' in html
    assert 'afip_research_data_dashboard.html' in html
