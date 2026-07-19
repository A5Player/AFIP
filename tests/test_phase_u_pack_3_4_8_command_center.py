from pathlib import Path

from afip.dashboard_ui.home import HOME_FILENAME, render_dashboard_home, write_dashboard_home


def test_command_center_embeds_three_split_dashboards():
    html = render_dashboard_home()
    assert "AFIP Command Center" in html
    assert 'src="afip_profiles_dashboard.html"' in html
    assert "afip_intelligence_engine_dashboard.html" in html
    assert "afip_research_data_dashboard.html" in html
    assert "data-page=\"operations\"" in html
    assert "data-page=\"intelligence\"" in html
    assert "data-page=\"research\"" in html


def test_command_center_is_presentation_only():
    html = render_dashboard_home()
    assert "No MT5 or execution-authority mutation" in html
    assert "order_send" not in html
    assert "AutomaticResearchRuntime" not in html


def test_write_command_center(tmp_path: Path):
    path = write_dashboard_home(tmp_path)
    assert path == tmp_path / HOME_FILENAME
    assert path.exists()
    assert "afip_profiles_dashboard.html" in path.read_text(encoding="utf-8")
