from afip.dashboard_ui import DashboardUIRuntime
from afip.partial_close import PartialCloseRuntime


def _buy(**extra):
    record = {
        "broker": "XM",
        "symbol": "GOLD#",
        "position_side": "BUY",
        "current_units": 3,
        "requested_close_units": 2,
        "minimum_remaining_units": 1,
        "entry_price": 2400.0,
        "current_price": 2420.0,
        "minimum_profit_distance": 5.0,
        "trading_cost": 1.0,
        "maximum_trading_cost": 2.0,
        "partial_close_action": "PARTIAL_CLOSE",
        "risk_allowed": True,
        "timing_allowed": True,
        "market_structure_confirmed": True,
    }
    record.update(extra)
    return record


def test_buy_partial_close_preserves_runner_in_simulation_only():
    report = PartialCloseRuntime().evaluate_one(_buy())
    assert report.status == "READY"
    assert report.partial_close_readiness == "READY"
    assert report.approved_close_units == 2
    assert report.remaining_units == 1
    assert report.partial_close_approved is True
    assert report.estimated_net_realized_profit == 38.0
    assert report.order_status == "NO_ORDER_SENT"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False


def test_sell_partial_close_uses_inverse_profit_direction():
    report = PartialCloseRuntime().evaluate_one(
        _buy(position_side="SELL", entry_price=2400.0, current_price=2380.0)
    )
    assert report.status == "READY"
    assert report.side_validation_passed is True
    assert report.open_profit_distance == 20.0


def test_partial_close_cannot_close_all_units_or_remove_runner():
    all_units = PartialCloseRuntime().evaluate_one(_buy(requested_close_units=3))
    runner = PartialCloseRuntime().evaluate_one(_buy(requested_close_units=2, minimum_remaining_units=2))
    assert "partial_close_cannot_close_all_units" in all_units.block_reasons
    assert "minimum_runner_units_not_preserved" in runner.block_reasons


def test_profit_and_trading_cost_must_pass():
    loss = PartialCloseRuntime().evaluate_one(_buy(current_price=2390.0))
    cost = PartialCloseRuntime().evaluate_one(_buy(trading_cost=3.0, maximum_trading_cost=2.0))
    assert "minimum_profit_not_confirmed" in loss.block_reasons
    assert "trading_cost_not_approved" in cost.block_reasons


def test_fixed_unit_risk_timing_structure_and_live_guards():
    unit = PartialCloseRuntime().evaluate_one(_buy(lot_per_unit=0.02))
    risk = PartialCloseRuntime().evaluate_one(_buy(risk_allowed=False))
    timing = PartialCloseRuntime().evaluate_one(_buy(timing_allowed=False))
    structure = PartialCloseRuntime().evaluate_one(_buy(market_structure_confirmed=False))
    live = PartialCloseRuntime().evaluate_one(_buy(live_execution_enabled=True))
    assert "fixed_unit_policy" in unit.block_reasons
    assert "risk_not_approved" in risk.block_reasons
    assert "timing_not_approved" in timing.block_reasons
    assert "market_structure_not_confirmed" in structure.block_reasons
    assert "live_or_direct_execution_requested" in live.block_reasons


def test_hold_and_bilingual_explainability_are_visible():
    report = PartialCloseRuntime().evaluate_one(_buy(partial_close_action="HOLD", requested_close_units=0))
    assert report.status == "READY"
    assert report.partial_close_readiness == "MONITORING"
    assert report.partial_close_approved is False
    assert report.holding_reason_en
    assert report.holding_reason_th
    assert report.partial_close_reason_en
    assert report.partial_close_reason_th
    assert report.expected_next_action_en
    assert report.expected_next_action_th
    assert 0.0 <= report.confidence <= 100.0


def test_dashboard_contains_partial_close_panel():
    dashboard = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "partial_close" in {panel.panel_id for panel in dashboard.panels}
