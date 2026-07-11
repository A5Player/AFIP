from afip.dashboard_ui import DashboardUIRuntime

EXPECTED_PANEL_IDS = {
    "production_readiness_complete",
    "knowledge_intelligence_foundation",
    "pattern_knowledge_engine",
    "pattern_similarity_search",
    "pattern_clustering",
    "pattern_statistics",
}


def test_regression_panels_are_registered_without_execution_authority():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    panel_ids = {panel.panel_id for panel in report.panels}
    assert EXPECTED_PANEL_IDS <= panel_ids
    assert report.live_execution_enabled is False
