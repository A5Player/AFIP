from pathlib import Path
from afip.dashboard_ui.dashboard_authority import DashboardAuthority, POLICY_VERSION
from afip.dashboard_ui.home import render_dashboard_home
from afip.dashboard_ui.launcher import launch_three_dashboards

def test_single_authority_builds_all_dashboard_outputs(tmp_path: Path):
    result = DashboardAuthority().build_all(tmp_path / 'out', project_root=tmp_path)
    assert result.policy_version == POLICY_VERSION
    for path in (result.home, result.profiles, result.intelligence, result.research, result.research_operations, result.cross_market):
        assert path.exists()

def test_legacy_launcher_delegates_and_remains_compatible(tmp_path: Path):
    p1, p2, p3 = launch_three_dashboards(tmp_path / 'out', project_root=tmp_path)
    assert p1.name == 'afip_profiles_dashboard.html'
    assert p2.name == 'afip_intelligence_engine_dashboard.html'
    assert p3.name == 'afip_research_data_dashboard.html'

def test_home_typography_is_compact_and_ellipsis_safe():
    html = render_dashboard_home()
    assert 'text-overflow:ellipsis' in html
    assert 'font-size:17px;line-height:1' in html
    assert 'white-space:nowrap' in html
