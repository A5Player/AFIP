from afip.paper_trading import PaperTradingEngineRuntime
from afip.dashboard_center import DashboardRuntimeStatus


def _paper_record(**overrides):
    record = {
        "broker": "XM",
        "symbol": "GOLD#",
        "profile_name": "Balanced",
        "mode": "PAPER",
        "paper_trading_requested": True,
        "paper_balance": 1000,
        "reserve": 200,
        "maximum_units": 3,
        "paper_orders": [
            {"order_id": "P1", "side": "BUY", "units": 2, "status": "MANAGING", "entry_price": 2300, "current_price": 2305, "confidence": 88, "risk_status": "risk_pass", "reason": "market_regime_and_signal_support_paper_hold"},
            {"order_id": "P2", "side": "SELL", "units": 1, "status": "WAITING", "entry_price": 2310, "current_price": 2310, "confidence": 61, "risk_status": "risk_review"},
        ],
    }
    record.update(overrides)
    return record


def test_paper_trading_runtime_keeps_live_execution_disabled():
    report = PaperTradingEngineRuntime().evaluate_one(_paper_record(live_execution_enabled=True))
    assert report.status == "BLOCKED"
    assert report.live_execution_enabled is False
    assert "live_execution_blocked_for_paper_trading" in report.validation_items


def test_paper_trading_blocks_non_xm_or_non_gold_version1_policy():
    report = PaperTradingEngineRuntime().evaluate_one(_paper_record(broker="Exness", symbol="XAUUSD"))
    assert report.status == "BLOCKED"
    assert "version1_xm_only_required" in report.validation_items
    assert "version1_gold_only_required" in report.validation_items


def test_paper_trading_uses_unit_system_not_direct_lot_increase():
    report = PaperTradingEngineRuntime().evaluate_one(_paper_record())
    first = report.orders[0]
    assert report.unit_lot == 0.01
    assert first.units == 2
    assert first.total_lot == 0.02
    assert "partial_close_uses_units" in first.partial_close_reason


def test_paper_order_lifecycle_contains_required_order_center_states():
    report = PaperTradingEngineRuntime().evaluate_one(_paper_record())
    states = [state.state for state in report.orders[0].lifecycle]
    assert states == ["WAITING", "READY", "OPENED", "MANAGING"]
    assert report.waiting_count == 1
    assert report.managing_count == 1


def test_paper_orders_explain_holding_stop_loss_trailing_and_exit():
    order = PaperTradingEngineRuntime().evaluate_one(_paper_record()).orders[0]
    assert order.holding_reason
    assert order.stop_loss_reason
    assert order.break_even_reason
    assert order.trailing_reason
    assert order.exit_reason
    assert order.current_ai_reasoning == "market_regime_and_signal_support_paper_hold"


def test_paper_portfolio_integrates_afip_bank_values():
    report = PaperTradingEngineRuntime().evaluate_one(_paper_record())
    assert report.balance >= 1000
    assert report.equity >= report.balance
    assert report.reserve == 200
    assert report.allocation == report.equity - report.reserve
    assert "afip_bank" in report.dashboard_sections


def test_dashboard_runtime_includes_paper_trading_dependency():
    report = DashboardRuntimeStatus().evaluate_one(_paper_record(research_center_requested=False))
    assert report.paper_trading_status == "READY"
    assert "order_center" in report.order_center_sections
    assert report.live_execution_enabled is False
