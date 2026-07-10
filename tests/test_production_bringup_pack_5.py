from afip.dashboard_ui import DashboardUIRuntime
from afip.explainable_order_center import ExplainableOrderCenterRuntime


def sample_record():
    return {
        "broker": "XM",
        "symbol": "GOLD#",
        "mode": "PAPER",
        "paper_trading_requested": True,
        "profile_name": "Balanced",
        "maximum_units": 3,
        "paper_orders": [
            {
                "order_id": "PAPER-EXPLAIN-1",
                "side": "BUY",
                "status": "MANAGING",
                "units": 2,
                "entry_price": 2300.0,
                "current_price": 2304.0,
                "confidence": 88.5,
                "risk_status": "risk_pass",
                "waiting_reason": "spread_inside_threshold",
                "entry_reason": "market_regime_and_risk_policy_aligned",
                "holding_reason": "trend_and_risk_remain_valid",
                "stop_loss_move_reason": "protect_capital_after_price_moves_in_favor",
                "take_profit_change_reason": "target_review_waits_for_market_structure_confirmation",
                "trailing_stop_reason": "trailing_review_after_profit_protection_threshold",
                "partial_close_reason": "partial_close_uses_unit_count_only",
                "exit_reason": "exit_not_confirmed_until_market_reason_changes",
                "expected_next_action": "continue_holding_review",
                "next_review_time": "2026-07-10T15:00:00+00:00",
            }
        ],
    }


def test_explainable_order_center_returns_bilingual_required_fields():
    report = ExplainableOrderCenterRuntime().evaluate_one(sample_record())

    assert report.status == "READY"
    assert report.reason == "explainable_order_center_ready"
    assert report.live_execution_enabled is False
    assert report.order_count == 1
    assert "waiting_reason" in report.visible_explanation_fields
    assert "entry_reason" in report.visible_explanation_fields
    assert "holding_reason" in report.visible_explanation_fields
    assert "stop_loss_move_reason" in report.visible_explanation_fields
    assert "take_profit_change_reason" in report.visible_explanation_fields
    assert "trailing_stop_reason" in report.visible_explanation_fields
    assert "partial_close_reason" in report.visible_explanation_fields
    assert "exit_reason" in report.visible_explanation_fields
    assert "expected_next_action" in report.visible_explanation_fields
    assert "confidence" in report.visible_explanation_fields
    assert "risk" in report.visible_explanation_fields
    assert "next_review_time" in report.visible_explanation_fields
    values = {item.key: item for item in report.orders[0].explanations}
    assert values["entry_reason"].title_th == "เหตุผลการเข้าเทรด"
    assert values["holding_reason"].explanation_en.startswith("Explains why")
    assert values["risk"].value == "risk_pass"


def test_explainable_order_center_blocks_live_execution():
    record = sample_record()
    record["mode"] = "LIVE"
    record["live_execution_enabled"] = True

    report = ExplainableOrderCenterRuntime().evaluate_one(record)

    assert report.status == "BLOCKED"
    assert report.reason == "live_execution_disabled_for_explainable_order_center"
    assert report.live_execution_enabled is False
    assert report.trading_logic_changed is False


def test_explainable_order_center_enforces_xm_gold_only():
    record = sample_record()
    record["broker"] = "EXNESS"

    report = ExplainableOrderCenterRuntime().evaluate_one(record)

    assert report.status == "BLOCKED"
    assert report.reason == "version1_xm_only_required"


def test_explainable_order_center_uses_units_not_direct_lot_increase():
    record = sample_record()
    record["paper_orders"][0]["units"] = 3

    report = ExplainableOrderCenterRuntime().evaluate_one(record)
    order = report.orders[0]

    assert order.units == 3
    assert order.lot_per_unit == 0.01
    assert order.total_lot == 0.03


def test_dashboard_renders_explainable_order_center_bilingual_panel():
    dashboard = DashboardUIRuntime().evaluate_one(sample_record())
    panel = next(item for item in dashboard.panels if item.panel_id == "explainable_order_center")

    assert panel.status == "READY"
    assert panel.title_en == "Explainable Order Center"
    assert panel.title_th == "ศูนย์คำสั่งแบบอธิบายได้"
    rendered = "\n".join(f"{key}: {value}" for key, value in panel.rows)
    assert "Entry Reason / เหตุผลการเข้าเทรด" in rendered
    assert "Holding Reason / เหตุผลการถือสถานะ" in rendered
    assert "Stop Loss Move Reason / เหตุผลการเลื่อน Stop Loss" in rendered
    assert "Take Profit Change Reason / เหตุผลการปรับ Take Profit" in rendered
    assert "Expected Next Action / การกระทำถัดไป" in rendered


def test_dashboard_html_contains_no_black_box_order_explainability():
    html = DashboardUIRuntime().render_html(sample_record())

    assert "Explainable Order Center" in html
    assert "ศูนย์คำสั่งแบบอธิบายได้" in html
    assert "Entry Reason" in html
    assert "เหตุผลการเข้าเทรด" in html
    assert "Live Execution: False" in html
