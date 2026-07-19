from pathlib import Path

from afip.dashboard_ui.home import render_dashboard_home
from afip.dashboard_ui.launcher import launch_three_dashboards


def test_dashboard_home_links_all_three_pages():
    html = render_dashboard_home()
    assert "afip_profiles_dashboard.html" in html
    assert "afip_intelligence_engine_dashboard.html" in html
    assert "afip_research_data_dashboard.html" in html
    assert "AFIP Dashboard Home" in html


def test_dashboard_generation_does_not_run_research_by_default(tmp_path: Path, monkeypatch):
    called = []

    def forbidden_run(self):
        called.append(True)
        raise AssertionError("research must not run during normal dashboard generation")

    monkeypatch.setattr("afip.dashboard_ui.launcher.AutomaticResearchRuntime.run", forbidden_run)
    p1, p2, p3 = launch_three_dashboards(tmp_path / "out", project_root=tmp_path)
    assert not called
    assert p1.exists() and p2.exists() and p3.exists()
    assert (tmp_path / "out" / "afip_dashboard.html").exists()


def test_explicit_research_bootstrap_remains_available(tmp_path: Path, monkeypatch):
    called = []
    monkeypatch.setattr("afip.dashboard_ui.launcher.AutomaticResearchRuntime.run", lambda self: called.append(True))
    launch_three_dashboards(tmp_path / "out", project_root=tmp_path, run_research_bootstrap=True)
    assert called == [True]
