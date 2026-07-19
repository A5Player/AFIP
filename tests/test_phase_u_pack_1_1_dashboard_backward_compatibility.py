from afip.dashboard_ui.runtime import DashboardUIRuntime


def test_phase_u_dashboard_preserves_milestone_h_pack_9_contract() -> None:
    html = DashboardUIRuntime().render_html({"mode": "SIMULATION", "broker": "XM", "symbol": "GOLD#"})
    assert "AFIP Dashboard — Milestone H Pack 9" in html


def test_phase_u_dashboard_preserves_milestone_h_pack_10_contract() -> None:
    html = DashboardUIRuntime().render_html({"mode": "SIMULATION", "broker": "XM", "symbol": "GOLD#"})
    assert "AFIP Dashboard — Milestone H Pack 10" in html


def test_phase_u_dashboard_keeps_new_runtime_integration_title_and_matrix() -> None:
    html = DashboardUIRuntime().render_html({"mode": "SIMULATION", "broker": "XM", "symbol": "GOLD#"})
    assert "AFIP Dashboard — Phase U Runtime Integration" in html
    assert "Runtime Coverage Matrix" in html
    assert 'data-dashboard-compatibility="milestone-h-pack-9-10"' in html
