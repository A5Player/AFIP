from pathlib import Path

from afip.dashboard_ui.split_runtime import (
    DASHBOARD_1_FILENAME,
    DASHBOARD_2_FILENAME,
    TwoDashboardRuntime,
)


def _record():
    return {
        "broker": "XM", "symbol": "GOLD#", "mode": "DEMO", "execution_mode": "DEMO",
        "profiles": [
            {"profile_id": f"P{i}", "profile_name": f"Profile {i}", "runtime_state": "RUNNING", "mt5_connection": "CONNECTED", "demo_gateway_status": "WAITING", "account": str(1000+i), "server": "XMGlobal-MT5 5", "data_fresh": True}
            for i in range(1, 5)
        ],
    }


def test_dashboard_one_is_separate_and_refreshes_every_five_seconds():
    html = TwoDashboardRuntime().render_profiles_html(_record())
    assert "AFIP Dashboard 1 — P1–P4 Operational Detail" in html
    assert '<meta http-equiv="refresh" content="5">' in html
    assert all(f"P{i} — Profile {i}" in html for i in range(1, 5))
    assert DASHBOARD_2_FILENAME in html


def test_dashboard_two_is_manual_refresh_and_contains_categories():
    html = TwoDashboardRuntime().render_intelligence_html(_record())
    assert "AFIP Dashboard 2 — Intelligence, Engines, Research & Data" in html
    assert "window.location.reload()" in html
    assert 'http-equiv="refresh"' not in html
    assert "Intelligence" in html
    assert "Engines" in html
    assert "Research &amp; Data" in html
    assert DASHBOARD_1_FILENAME in html


def test_writes_two_distinct_html_files(tmp_path: Path):
    paths = TwoDashboardRuntime().write_dashboards(_record(), tmp_path)
    assert paths[0].name == DASHBOARD_1_FILENAME
    assert paths[1].name == DASHBOARD_2_FILENAME
    assert paths[0] != paths[1]
    assert all(path.exists() for path in paths)


def test_execution_authority_is_not_added():
    source = Path("afip/dashboard_ui/split_runtime.py").read_text(encoding="utf-8")
    assert "order_send(" not in source
    assert "order_check(" not in source
    assert "positions_close(" not in source
