from pathlib import Path

from afip.dashboard_ui import DashboardUIRuntime, launch_dashboard


def _dashboard_record(**overrides):
    record = {
        "broker": "XM",
        "symbol": "GOLD#",
        "profile_name": "Balanced",
        "mode": "PAPER",
        "market_regime": "TRENDING",
        "paper_trading_requested": True,
        "paper_balance": 1000,
        "reserve": 200,
        "maximum_units": 3,
        "research_center_requested": True,
        "historical_dataset_ready": True,
        "walk_forward_ready": True,
        "completed_research_orders": 120,
        "paper_orders": [
            {"order_id": "P1", "side": "BUY", "units": 2, "status": "MANAGING", "entry_price": 2300, "current_price": 2306, "confidence": 88, "risk_status": "risk_pass", "reason": "market_regime_and_signal_support_paper_hold"}
        ],
    }
    record.update(overrides)
    return record


def test_dashboard_ui_renders_visible_html_launcher_without_live_execution():
    report = DashboardUIRuntime().evaluate_one(_dashboard_record())
    html = DashboardUIRuntime().render_html(_dashboard_record())
    assert report.visible_dashboard_ready is True
    assert report.live_execution_enabled is False
    assert "AFIP Dashboard" in html
    assert "Live Execution: False" in html


def test_dashboard_ui_blocks_live_execution_and_non_version1_policy():
    report = DashboardUIRuntime().evaluate_one(_dashboard_record(broker="Exness", symbol="XAUUSD", mode="LIVE", live_execution_enabled=True))
    assert report.status == "BLOCKED"
    assert report.live_execution_enabled is False
    assert report.panels[0].panel_id == "policy"
    assert "version1_xm_only_required" in dict(report.panels[0].rows)


def test_dashboard_ui_contains_required_navigation_sections():
    report = DashboardUIRuntime().evaluate_one(_dashboard_record())
    assert report.navigation_sections == ("Runtime", "Intelligence", "Trading", "Analytics", "AFIP Bank", "Research", "System", "Market", "Order Center")


def test_dashboard_ui_panels_have_thai_and_english_titles_and_descriptions():
    report = DashboardUIRuntime().evaluate_one(_dashboard_record())
    assert all(panel.title_en and panel.title_th for panel in report.panels)
    assert all(panel.description_en and panel.description_th for panel in report.panels)


def test_dashboard_ui_order_center_explains_holding_risk_and_next_action():
    report = DashboardUIRuntime().evaluate_one(_dashboard_record())
    order_panel = next(panel for panel in report.panels if panel.panel_id == "order_center")
    rows = dict(order_panel.rows)
    assert rows["P1 Status"] == "MANAGING"
    assert rows["P1 Holding Reason"]
    assert rows["P1 Expected Next Action"]
    assert rows["P1 Risk"] == "risk_pass"


def test_dashboard_ui_bank_panel_displays_afip_bank_values():
    report = DashboardUIRuntime().evaluate_one(_dashboard_record())
    bank_panel = next(panel for panel in report.panels if panel.panel_id == "afip_bank")
    rows = dict(bank_panel.rows)
    assert "Balance" in rows
    assert "Equity" in rows
    assert "Reserve" in rows
    assert "ROI" in rows


def test_dashboard_ui_launcher_writes_html_file(tmp_path: Path):
    output = tmp_path / "afip_dashboard.html"
    path = launch_dashboard(output, _dashboard_record())
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "Dashboard Runtime" in content
    assert "Order Center" in content
