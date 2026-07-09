"""Production Milestone H Pack 10 — Production Readiness tests."""

from __future__ import annotations

from afip.dashboard_ui import DashboardUIRuntime
from afip.production_readiness import ProductionReadinessRuntime


def _record(**overrides):
    base = {
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "DEMO",
        "execution_mode": "DEMO",
        "market_regime": "TRENDING",
        "signal_context": "BUY_EDGE",
        "profile_name": "Balanced",
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
        "dashboard_enabled": True,
        "logging_enabled": True,
        "backup_enabled": True,
        "setup_completed_steps": ("welcome", "broker", "login", "password", "mt5_path", "download_historical_data", "profile_selection", "test_connection", "save", "run_afip"),
        "internet_status": "CONNECTED",
        "mt5_status": "CONNECTED",
        "broker_status": "XM_READY",
        "connection_test_passed": True,
        "saved": True,
        "vps_ready": True,
        "windows_vps_ready": True,
        "historical_data_ready": True,
        "history_ready": True,
        "historical_research_ready": True,
        "walk_forward_ready": True,
        "download_requested": True,
        "historical_download_requested": True,
        "requested_days": 1,
        "downloaded_bars": 144,
        "missing_bars": 0,
        "duplicate_bars": 0,
        "invalid_bars": 0,
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
        "demo_trading_requested": True,
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


def test_production_readiness_marks_pack_10_release_candidate_when_workflow_is_ready():
    report = ProductionReadinessRuntime().evaluate_one(_record())
    assert report.status == "READY"
    assert report.release_stage == "VERSION_1_RELEASE_CANDIDATE"
    assert report.vps_ready is True
    assert report.historical_data_ready is True
    assert report.walk_forward_ready is True
    assert report.research_ready is True
    assert report.paper_trading_ready is True
    assert report.dashboard_ready is True
    assert report.demo_trading_ready is True


def test_production_readiness_blocks_live_execution_and_non_version1_policy():
    report = ProductionReadinessRuntime().evaluate_one(_record(broker="Exness", symbol="XAUUSD", mode="LIVE", live_execution_enabled=True))
    assert report.status == "BLOCKED"
    assert "version1_xm_only_required" in report.validation_items
    assert "version1_gold_only_required" in report.validation_items
    assert "live_execution_blocked_for_pack_10" in report.validation_items
    assert report.live_execution_enabled is False


def test_demo_trading_readiness_allows_demo_without_live_order_execution():
    demo = ProductionReadinessRuntime().evaluate_one(_record()).demo_readiness
    assert demo.status == "READY"
    assert demo.execution_mode == "DEMO"
    assert demo.demo_order_enabled is True
    assert demo.live_execution_enabled is False
    assert demo.reason == "demo_trading_ready_without_live_execution"


def test_deployment_steps_cover_vps_historical_walk_forward_research_paper_dashboard_demo_and_live_block():
    report = ProductionReadinessRuntime().evaluate_one(_record())
    ids = {step.step_id: step.status for step in report.deployment_steps}
    assert ids["vps_deployment"] == "READY"
    assert ids["historical_download"] == "READY"
    assert ids["walk_forward"] == "READY"
    assert ids["research"] == "READY"
    assert ids["paper_trading"] == "READY"
    assert ids["dashboard"] == "READY"
    assert ids["demo_trading"] == "READY"
    assert ids["live_trading"] == "BLOCKED"


def test_handoff_items_define_safe_vps_workflow_before_live_trading():
    report = ProductionReadinessRuntime().evaluate_one(_record())
    assert report.handoff_items == (
        "deploy_to_vps",
        "download_historical_data",
        "run_walk_forward",
        "run_research",
        "run_paper_trading",
        "run_demo_trading",
        "do_not_enable_live_trading",
    )
    assert report.trading_logic_changed is False


def test_dashboard_ui_includes_production_readiness_panel():
    report = DashboardUIRuntime().evaluate_one(_record())
    panel_ids = {panel.panel_id for panel in report.panels}
    assert "production_readiness" in panel_ids
    assert "Production Readiness" in report.navigation_sections
    panel = next(panel for panel in report.panels if panel.panel_id == "production_readiness")
    assert any(key == "Demo Trading" and value == "True" for key, value in panel.rows)
    assert any(key == "Live Execution" and value == "False" for key, value in panel.rows)


def test_dashboard_ui_html_renders_pack_10_without_changing_trading_logic():
    html = DashboardUIRuntime().render_html(_record())
    report = DashboardUIRuntime().evaluate_one(_record())
    assert "AFIP Dashboard — Milestone H Pack 10" in html
    assert "Production Readiness" in html
    assert "Live Execution: False" in html
    assert report.trading_logic_changed is False
    assert report.live_execution_enabled is False
