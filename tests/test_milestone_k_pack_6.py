from afip.dashboard_ui import DashboardUIRuntime
from afip.trailing_stop import TrailingStopRuntime


def _buy(**extra):
    record = {
        "broker": "XM",
        "symbol": "GOLD#",
        "position_side": "BUY",
        "current_units": 2,
        "entry_price": 2400.0,
        "current_price": 2430.0,
        "current_stop_loss": 2390.0,
        "proposed_trailing_stop": 2415.0,
        "minimum_locked_profit": 10.0,
        "trading_cost": 1.0,
        "maximum_trading_cost": 2.0,
        "trailing_stop_action": "TRAIL_STOP",
        "risk_allowed": True,
        "timing_allowed": True,
        "market_structure_confirmed": True,
    }
    record.update(extra)
    return record


def test_buy_trailing_stop_locks_profit_in_simulation_only():
    report = TrailingStopRuntime().evaluate_one(_buy())
    assert report.status == "READY"
    assert report.trailing_stop_readiness == "READY"
    assert report.break_even_detected is True
    assert report.profit_lock_active is True
    assert report.change_approved is True
    assert report.estimated_locked_profit == 14.0
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False


def test_sell_trailing_stop_validates_inverse_geometry():
    report = TrailingStopRuntime().evaluate_one(
        _buy(
            position_side="SELL",
            entry_price=2400.0,
            current_price=2370.0,
            current_stop_loss=2410.0,
            proposed_trailing_stop=2385.0,
        )
    )
    assert report.status == "READY"
    assert report.side_validation_passed is True
    assert report.estimated_locked_profit == 14.0


def test_buy_trailing_stop_cannot_move_away_from_profit():
    report = TrailingStopRuntime().evaluate_one(_buy(proposed_trailing_stop=2385.0))
    assert report.status == "BLOCKED"
    assert "trailing_stop_does_not_reduce_buy_risk" in report.block_reasons


def test_minimum_locked_profit_and_cost_are_enforced():
    profit_report = TrailingStopRuntime().evaluate_one(_buy(minimum_locked_profit=20.0))
    cost_report = TrailingStopRuntime().evaluate_one(_buy(trading_cost=3.0, maximum_trading_cost=2.0))
    assert "minimum_locked_profit_not_met" in profit_report.block_reasons
    assert "trading_cost_not_approved" in cost_report.block_reasons


def test_risk_timing_structure_and_live_requests_are_blocked():
    risk = TrailingStopRuntime().evaluate_one(_buy(risk_allowed=False))
    timing = TrailingStopRuntime().evaluate_one(_buy(timing_allowed=False))
    structure = TrailingStopRuntime().evaluate_one(_buy(market_structure_confirmed=False))
    live = TrailingStopRuntime().evaluate_one(_buy(live_execution_enabled=True))
    assert "risk_not_approved" in risk.block_reasons
    assert "timing_not_approved" in timing.block_reasons
    assert "market_structure_not_confirmed" in structure.block_reasons
    assert "live_or_direct_execution_requested" in live.block_reasons


def test_multi_stage_and_bilingual_explainability_are_visible():
    report = TrailingStopRuntime().evaluate_one(_buy(trailing_stage=4))
    assert report.trailing_stage == 4
    assert report.trailing_stage_name == "STRUCTURE_TRAILING"
    assert report.holding_reason_en
    assert report.holding_reason_th
    assert report.trailing_stop_reason_en
    assert report.trailing_stop_reason_th
    assert report.expected_next_action_en
    assert report.expected_next_action_th
    assert 0.0 <= report.confidence <= 100.0


def test_dashboard_contains_trailing_stop_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "trailing_stop" in {panel.panel_id for panel in dashboard.panels}
