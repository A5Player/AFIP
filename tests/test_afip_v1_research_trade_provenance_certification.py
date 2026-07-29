from __future__ import annotations

from afip.demo_execution_gateway.runtime import DemoExecutionGateway, DemoGatewayReport


class _Info:
    trade_tick_size = 0.01
    trade_tick_value = 1.0
    trade_tick_value_loss = 1.0


class _MT5:
    @staticmethod
    def symbol_info(_symbol):
        return _Info()


def test_trade_provenance_extracts_research_identity_and_metrics():
    result = {
        "market_regime": "TRENDING",
        "pattern": {"pattern_id": "PAT-17", "pattern_name": "Bullish Pullback", "pattern_family": "TREND_CONTINUATION"},
        "research": {
            "ranking_id": "RANK-2026-07-29",
            "selected_plan_id": "PLAN-017",
            "eligible_rank": 1,
            "rank": 2,
            "evidence_count": 1284,
            "win_rate": 74.1,
            "profit_factor": 2.18,
            "maximum_drawdown_percent": 6.4,
            "selection_reason": "highest eligible risk-adjusted plan",
        },
    }
    protection = {"stop_loss_source": "ATR_BUFFER_V3", "take_profit_source": "RESEARCH_EXIT_MODEL_V2"}
    value = DemoExecutionGateway._trade_provenance(result, protection)
    assert value["pattern_id"] == "PAT-17"
    assert value["pattern_name"] == "Bullish Pullback"
    assert value["research_ranking_id"] == "RANK-2026-07-29"
    assert value["research_eligible_rank"] == 1
    assert value["research_evidence_count"] == 1284
    assert value["sl_authority"] == "ATR_BUFFER_V3"
    assert value["tp_authority"] == "RESEARCH_EXIT_MODEL_V2"
    assert value["research_authority_status"] == "RECORDED"


def test_protection_financials_reports_prices_points_and_usd():
    requests = [
        {"symbol": "GOLD#", "price": 2400.00, "sl": 2397.00, "tp": 2405.00, "volume": 0.01},
        {"symbol": "GOLD#", "price": 2400.00, "sl": 2397.00, "tp": 2405.00, "volume": 0.01},
    ]
    value = DemoExecutionGateway._protection_financials(_MT5(), requests, 0.01)
    assert value["stop_loss_price"] == 2397.0
    assert value["take_profit_price"] == 2405.0
    assert value["stop_loss_price_distance"] == 3.0
    assert value["take_profit_price_distance"] == 5.0
    assert value["stop_loss_usd_per_order"] == (3.0, 3.0)
    assert value["take_profit_usd_per_order"] == (5.0, 5.0)
    assert value["total_stop_loss_usd"] == 6.0
    assert value["total_take_profit_usd"] == 10.0


def test_missing_research_evidence_is_not_invented():
    value = DemoExecutionGateway._trade_provenance({}, {})
    assert value["research_authority_status"] == "NOT_RECORDED"
    assert value["research_evidence_count"] is None
    assert value["research_win_rate"] is None
    assert value["sl_authority"] == "NOT_RECORDED"
    assert value["tp_authority"] == "NOT_RECORDED"


def test_gateway_report_serializes_trade_provenance_fields():
    report = DemoGatewayReport(
        profile_id="P1", status="ORDER_SENT", reason="protected_demo_orders_sent",
        account="****0001", server="XMGlobal-MT5 6", symbol="GOLD#", armed=True,
        plan_id="PLAN-017", pattern_id="PAT-17", research_eligible_rank=1,
        sl_authority="ATR_BUFFER_V3", tp_authority="RESEARCH_EXIT_MODEL_V2",
        stop_loss_price=2397.0, take_profit_price=2405.0,
        total_stop_loss_usd=3.0, total_take_profit_usd=5.0,
    )
    payload = report.as_dict()
    assert payload["pattern_id"] == "PAT-17"
    assert payload["research_eligible_rank"] == 1
    assert payload["total_stop_loss_usd"] == 3.0
    assert payload["total_take_profit_usd"] == 5.0
