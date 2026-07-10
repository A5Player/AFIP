from afip.dashboard_ui import DashboardUIRuntime
from afip.dynamic_stop_loss import DynamicStopLossRuntime


def _base(**extra):
    record = {
        "position_side": "BUY",
        "current_units": 2,
        "reference_price": 2400.0,
        "current_stop_loss": 2380.0,
        "proposed_stop_loss": 2390.0,
        "stop_loss_action": "MOVE_STOP_LOSS",
    }
    record.update(extra)
    return record


def test_buy_move_reduces_risk_and_is_simulation_only():
    r = DynamicStopLossRuntime().evaluate_one(_base())
    assert r.status == "READY"
    assert r.move_approved is True
    assert r.risk_reduction == 10.0
    assert r.no_order_sent is True


def test_buy_move_cannot_loosen_risk():
    r = DynamicStopLossRuntime().evaluate_one(_base(proposed_stop_loss=2370.0))
    assert "buy_stop_loss_move_invalid" in r.block_reasons
    assert "stop_loss_move_must_reduce_risk" in r.block_reasons


def test_sell_move_must_remain_above_market_and_reduce_risk():
    r = DynamicStopLossRuntime().evaluate_one(_base(position_side="SELL", current_stop_loss=2420.0, proposed_stop_loss=2410.0))
    assert r.status == "READY" and r.move_approved is True


def test_market_structure_confirmation_is_required_for_move():
    r = DynamicStopLossRuntime().evaluate_one(_base(market_structure_confirmed=False))
    assert "market_structure_not_confirmed" in r.block_reasons


def test_live_request_is_blocked():
    r = DynamicStopLossRuntime().evaluate_one(_base(live_execution_enabled=True))
    assert "live_or_direct_execution_requested" in r.block_reasons


def test_dashboard_contains_dynamic_stop_loss_panel():
    report = DashboardUIRuntime().evaluate_one({"broker": "XM", "symbol": "GOLD#", "mode": "PAPER"})
    assert "dynamic_stop_loss" in {p.panel_id for p in report.panels}
