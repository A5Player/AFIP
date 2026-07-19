from afip.dashboard_ui.split_runtime import SplitDashboardRenderer


def test_dashboard_1_uses_single_line_profile_table() -> None:
    renderer = SplitDashboardRenderer()
    html = renderer.render_profiles_html({"profiles": [
        {"profile_id": f"P{i}", "profile_name": f"Profile {i}", "runtime_state": "RUNNING"}
        for i in range(1, 5)
    ]})
    assert 'class="profile-table"' in html
    assert '.profile-table th,.profile-table td{white-space:nowrap' in html
    assert 'text-overflow:ellipsis' in html
    assert 'title="' in html


def test_dashboard_3_uses_balanced_single_line_grids() -> None:
    renderer = SplitDashboardRenderer()
    html = renderer.render_research_html({}, project_root='.')
    assert 'class="research-grid"' in html
    assert 'class="research-evidence-grid"' in html
    assert '.research-grid .panel{height:360px' in html
    assert '.research-evidence-grid .panel{height:360px' in html
    assert '.research-grid .panel td{padding:3px 4px;line-height:1.08;white-space:nowrap' in html
    assert '.research-evidence-grid .panel td{padding:3px 4px;line-height:1.08;white-space:nowrap' in html


def test_renderer_compatibility_name_is_preserved() -> None:
    assert SplitDashboardRenderer.__name__ == "SplitDashboardRenderer"
