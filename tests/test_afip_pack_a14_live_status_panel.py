from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def test_pages_poll_only_the_live_status_panel() -> None:
    renderer = ThreeDashboardRuntime()
    for html in (
        renderer.render_profiles_html({}),
        renderer.render_intelligence_html({}),
        renderer.render_research_html({}, "."),
    ):
        assert 'http-equiv="refresh" content="5"' not in html
        assert 'AFIP_LIVE_STATUS_POLL_V1' in html
        assert 'afip_live_status.html' in html
