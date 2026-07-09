"""Production Milestone H Pack 9 — Dashboard Intelligence Integration tests."""

from __future__ import annotations

from afip.dashboard_intelligence import DashboardIntelligenceRuntime
from afip.dashboard_ui import DashboardUIRuntime


def _record(**overrides):
    base = {
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "PAPER",
        "execution_mode": "PAPER",
        "market_regime": "TRENDING",
        "signal_context": "BUY_EDGE",
        "profile_name": "Balanced",
        "profile_type": "Balanced",
        "server": "XMGlobal-MT5 6",
        "login": "123456",
        "password": "hidden",
        "mt5_terminal_path": "C:/Program Files/MetaTrader 5/terminal64.exe",
        "account_type": "Demo",
        "initial_capital": 1000.0,
        "capital_per_unit": 100.0,
        "maximum_units": 3,
        "split_orders": True,
        "overnight_holding": False,
        "risk_profile": "balanced",
        "ai_profile": "standard",
        "research_profile": "separated",
        "dashboard_enabled": True,
        "notification_enabled": True,
        "logging_enabled": True,
        "backup_enabled": True,
        "setup_completed_steps": ("welcome", "broker", "login", "password", "mt5_path", "download_historical_data", "profile_selection", "test_connection", "save", "run_afip"),
        "internet_status": "CONNECTED",
        "mt5_status": "CONNECTED",
        "broker_status": "XM_READY",
        "historical_data_ready": True,
        "history_ready": True,
        "connection_test_passed": True,
        "saved": True,
        "historical_download_requested": True,
        "requested_days": 1,
        "downloaded_bars": 144,
        "missing_bars": 0,
        "duplicate_bars": 0,
        "invalid_bars": 0,
        "historical_research_ready": True,
        "walk_forward_ready": True,
        "download_requested": True,
        "timeframes": ("M1", "M5", "M15", "H1", "H4", "D1"),
        "bars": {
            "M1": [(1, 1.0, 2.0, 0.5, 1.5)],
            "M5": [(1, 1.0, 2.0, 0.5, 1.5)],
            "M15": [(1, 1.0, 2.0, 0.5, 1.5)],
            "H1": [(1, 1.0, 2.0, 0.5, 1.5)],
            "H4": [(1, 1.0, 2.0, 0.5, 1.5)],
            "D1": [(1, 1.0, 2.0, 0.5, 1.5)],
        },
        "research_center_requested": True,
        "completed_research_orders": 120,
        "research_orders": tuple(
            {
                "scope": "RESEARCH",
                "trading_hour": "10:00",
                "trading_session": "London",
                "market_regime": "TRENDING",
                "entry_plan": "pullback",
                "exit_plan": "trailing",
                "pattern": "higher_highs_higher_lows",
                "engine_combination": "smc_fvg_trend",
                "profit_reason": "trend_continuation",
                "loss_reason": "spread_review",
                "profit": 1.0,
                "drawdown": 0.5,
                "risk_score": 1.0,
            }
            for _ in range(120)
        ),
        "paper_trading_requested": True,
        "paper_orders": (
            {
                "order_id": "PAPER-0001",
                "side": "BUY",
                "units": 2,
                "status": "MANAGING",
                "entry_price": 2400.0,
                "current_price": 2405.0,
                "confidence": 88.0,
                "quality": "A",
                "risk_status": "risk_pass",
                "holding_reason": "market_regime_and_risk_remain_valid",
                "stop_loss_reason": "stop_loss_protects_profile_capital",
                "trailing_reason": "trailing_waits_for_profit_protection_evidence",
                "partial_close_reason": "partial_close_uses_units_not_direct_lot_increase",
                "exit_reason": "exit_delayed_until_exit_reason_is_complete",
                "current_ai_reasoning": "buy_edge_remains_valid_after_runtime_review",
                "expected_next_action": "continue_managing_paper_position",
            },
        ),
        "confidence": 88.0,
        "accuracy": 72.5,
        "win_rate": 61.2,
        "market_status": "OPEN",
        "trading_session": "London",
    }
    base.update(overrides)
    return base


def test_dashboard_intelligence_integrates_all_pack_1_to_8_dependencies():
    report = DashboardIntelligenceRuntime().evaluate_one(_record())
    names = {row.english_name for row in report.engine_rows}
    assert report.status == "READY"
    assert "Runtime Service Manager" in names
    assert "Profile Manager" in names
    assert "Historical Data Manager" in names
    assert "Historical Download Pipeline" in names
    assert "Research Center" in names
    assert "Paper Trading Engine" in names
    assert report.afip_bank_status == "READY"


def test_dashboard_intelligence_blocks_live_execution_and_non_version1_policy():
    report = DashboardIntelligenceRuntime().evaluate_one(_record(broker="Exness", symbol="XAUUSD", mode="LIVE", live_execution_enabled=True))
    assert report.status == "BLOCKED"
    assert "version1_xm_only_required" in report.validation_items
    assert "version1_gold_only_required" in report.validation_items
    assert "live_execution_blocked_for_dashboard_intelligence" in report.validation_items
    assert report.live_execution_enabled is False


def test_dashboard_intelligence_engine_rows_fit_one_row_with_required_fields():
    report = DashboardIntelligenceRuntime().evaluate_one(_record())
    row = report.engine_rows[0]
    assert row.status_icon
    assert row.english_name
    assert row.thai_name
    assert row.description
    assert row.input
    assert row.output
    assert row.confidence == 88.0
    assert row.accuracy == 72.5
    assert row.win_rate == 61.2
    assert row.runtime
    assert row.waiting_reason
    assert row.dependency
    assert row.health
    assert row.research_statistics
    assert row.live_statistics


def test_dashboard_intelligence_separates_research_and_live_statistics():
    report = DashboardIntelligenceRuntime().evaluate_one(_record())
    assert report.research_statistics_scope == "RESEARCH_ONLY"
    assert report.live_statistics_scope == "LIVE_SEPARATE_NOT_USED_FOR_RESEARCH_RANKING"
    research_row = next(row for row in report.engine_rows if row.english_name == "Research Center")
    assert research_row.research_statistics == "RESEARCH_ONLY"
    assert research_row.live_statistics == "LIVE_SEPARATE_NOT_USED_FOR_RESEARCH_RANKING"


def test_dashboard_intelligence_explains_open_order_management_reasons():
    explanation = DashboardIntelligenceRuntime().evaluate_one(_record()).decision_explanation
    assert explanation.holding_reason == "market_regime_and_risk_remain_valid"
    assert explanation.stop_loss_reason == "stop_loss_protects_profile_capital"
    assert explanation.trailing_reason == "trailing_waits_for_profit_protection_evidence"
    assert explanation.partial_close_reason == "partial_close_uses_units_not_direct_lot_increase"
    assert explanation.exit_reason == "exit_delayed_until_exit_reason_is_complete"
    assert explanation.current_ai_reasoning == "buy_edge_remains_valid_after_runtime_review"
    assert explanation.expected_next_action == "continue_managing_paper_position"


def test_dashboard_ui_contains_integrated_intelligence_panel_and_explainability_navigation():
    report = DashboardUIRuntime().evaluate_one(_record())
    panel_ids = {panel.panel_id for panel in report.panels}
    assert "dashboard_intelligence" in panel_ids
    assert "Order Center" in report.navigation_sections
    panel = next(panel for panel in report.panels if panel.panel_id == "dashboard_intelligence")
    assert "Dashboard Intelligence Integration" == panel.title_en
    assert any("Paper Trading Engine" in key for key, _ in panel.rows)
    assert any(key == "Decision Holding" and value == "market_regime_and_risk_remain_valid" for key, value in panel.rows)


def test_dashboard_ui_html_renders_pack_9_integrated_runtime_without_trading_logic_change():
    runtime = DashboardUIRuntime()
    html = runtime.render_html(_record())
    report = runtime.evaluate_one(_record())
    assert "AFIP Dashboard — Milestone H Pack 9" in html
    assert "Dashboard Intelligence Integration" in html
    assert "Live Execution: False" in html
    assert report.trading_logic_changed is False
    assert report.live_execution_enabled is False
