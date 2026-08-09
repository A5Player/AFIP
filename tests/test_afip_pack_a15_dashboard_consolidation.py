from pathlib import Path

from afip.dashboard_ui.dashboard_authority import DashboardAuthority
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def _profiles() -> list[dict[str, object]]:
    return [
        {
            "profile_id": f"P{number}",
            "profile_name": f"Profile {number}",
            "runtime_state": "RUNNING",
            "mt5_connection": "CONNECTED",
            "account_balance": 100.0 * number,
            "account_equity": 101.0 * number,
            "free_margin": 99.0 * number,
            "currency": "USD",
            "data_fresh": True,
        }
        for number in range(1, 5)
    ]


def test_consolidated_views_keep_content_still_and_poll_only_status(tmp_path: Path) -> None:
    renderer = ThreeDashboardRuntime()
    pages = (
        renderer.render_profiles_html({"profiles": _profiles()}),
        renderer.render_intelligence_html({"profiles": _profiles(), "project_root": str(tmp_path)}),
        renderer.render_research_html({"profiles": _profiles()}, tmp_path),
    )
    for html in pages:
        assert '<meta http-equiv="refresh" content="5">' not in html
        assert "AFIP_LIVE_STATUS_POLL_V1" in html
    assert "P1–P4" in pages[0]
    assert "Data download, replay & integrity" in pages[1]
    assert "Pattern / plan ranking" in pages[2]


def test_ranking_uses_recorded_outcomes_and_never_invents_financial_values(tmp_path: Path) -> None:
    events = tmp_path / "runtime" / "research" / "events"
    events.mkdir(parents=True)
    (events / "records.jsonl").write_text(
        '\n'.join((
            '{"pattern_name":"Sweep rejection","outcome":"WIN","profit":12.5,"max_drawdown":4}',
            '{"pattern_name":"Sweep rejection","outcome":"LOSS","profit":-3.5,"max_drawdown":5}',
            '{"entry_plan":"Break acceptance","outcome":"WIN"}',
        )),
        encoding="utf-8",
    )
    html = ThreeDashboardRuntime().render_research_html({}, tmp_path)
    assert "Sweep rejection" in html
    assert "50.00%" in html
    assert "9.00" in html
    assert "DATA_UNAVAILABLE" in html


def test_live_build_keeps_legacy_minimal_renderer_compatible(tmp_path: Path, monkeypatch) -> None:
    class Renderer:
        def render_research_html(self, data, project_root):
            return "RESEARCH"
    monkeypatch.setattr("afip.dashboard_ui.split_runtime.ThreeDashboardRuntime", lambda: Renderer())
    monkeypatch.setattr("afip.dashboard_ui.home.render_dashboard_home", lambda: "HOME")
    monkeypatch.setattr("afip.dashboard_ui.research_operations.render_research_operations", lambda root: "OPERATIONS")
    monkeypatch.setattr("afip.dashboard_ui.launcher.default_dashboard_record", lambda: {})
    result = DashboardAuthority().build_live(tmp_path / "dashboard", project_root=tmp_path)
    assert set(result) == {"home", "research", "research_operations"}
