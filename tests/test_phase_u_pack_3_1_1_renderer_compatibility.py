from afip.dashboard_ui.split_runtime import SplitDashboardRenderer, ThreeDashboardRuntime


def test_split_dashboard_renderer_preserves_three_dashboard_runtime_contract():
    renderer = SplitDashboardRenderer()
    assert isinstance(renderer, ThreeDashboardRuntime)
    html = renderer.render_intelligence_html({})
    assert 'class="intelligence-grid"' in html
