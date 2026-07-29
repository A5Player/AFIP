from pathlib import Path

from afip.dashboard_ui.navigation import standalone_navigation
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _record(tmp_path: Path):
    profiles=[]
    for i in range(1,5):
        profiles.append({
            "profile_id": f"P{i}",
            "profile_name": f"Profile {i}",
            "runtime_state": "RUNNING",
            "process_alive": True,
            "financial_live": True,
            "sizing_authority": "CAPITAL_TIER_FORMULA_ONLY",
        })
    return {"profiles": profiles, "project_root": str(tmp_path)}


def test_shared_navigation_contains_required_pages():
    html=standalone_navigation("operations")
    for filename in (
        "afip_profiles_dashboard.html",
        "afip_intelligence_engine_dashboard.html",
        "afip_research_data_dashboard.html",
        "afip_research_operations_dashboard.html",
        "afip_control_center.html",
        "afip_dashboard.html",
    ):
        assert filename in html
    assert 'class="afip-side-link active"' in html


def test_profiles_dashboard_has_standalone_sidebar(tmp_path):
    html=ThreeDashboardRuntime().render_profiles_html(_record(tmp_path))
    assert "afip-standalone-sidebar" in html
    assert "Dashboard Navigation" in html
    assert "body.afip-embedded" in html
    assert "window.self!==window.top" in html


def test_intelligence_dashboard_has_standalone_sidebar(tmp_path):
    html=ThreeDashboardRuntime().render_intelligence_html(_record(tmp_path))
    assert "afip-standalone-sidebar" in html
    assert "Intelligence &amp; Engines" in html


def test_research_dashboard_has_standalone_sidebar(tmp_path):
    html=ThreeDashboardRuntime().render_research_html(_record(tmp_path), tmp_path)
    assert "afip-standalone-sidebar" in html
    assert "Research &amp; Data" in html
