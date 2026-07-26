from pathlib import Path

from afip.dashboard_ui.dashboard_authority import DashboardAuthority


def test_live_build_refreshes_only_priority_pages(tmp_path: Path, monkeypatch) -> None:
    class Renderer:
        def render_research_html(self, data, project_root): return "RESEARCH"
    monkeypatch.setattr("afip.dashboard_ui.split_runtime.ThreeDashboardRuntime", lambda: Renderer())
    monkeypatch.setattr("afip.dashboard_ui.home.render_dashboard_home", lambda: "HOME")
    monkeypatch.setattr("afip.dashboard_ui.research_operations.render_research_operations", lambda root: "OPERATIONS")
    monkeypatch.setattr("afip.dashboard_ui.launcher.default_dashboard_record", lambda: {})

    result = DashboardAuthority().build_live(tmp_path / "runtime/dashboard", project_root=tmp_path)
    assert set(result) == {"home", "research", "research_operations"}
    assert result["home"].read_text(encoding="utf-8") == "HOME"
    assert result["research"].read_text(encoding="utf-8") == "RESEARCH"
    assert result["research_operations"].read_text(encoding="utf-8") == "OPERATIONS"


def test_monitor_has_fast_and_full_intervals() -> None:
    source = Path("tools/afip_dashboard_monitor.py").read_text(encoding="utf-8")
    assert 'default=10.0' in source
    assert 'default=60.0' in source
    assert 'build_live' in source
    assert 'build_all' in source
    assert 'order_send_called": False' in source


def test_final_runtime_launches_dashboard_at_10_and_60_seconds() -> None:
    source = Path("afip/final_integration/runtime.py").read_text(encoding="utf-8")
    assert "'--fast-interval','10'" in source
    assert "'--full-interval','60'" in source
    assert "'refresh_interval_seconds':10" in source
