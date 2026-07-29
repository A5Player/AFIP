from __future__ import annotations

from types import SimpleNamespace

from afip.demo_execution_gateway.runtime import DemoExecutionGateway
from afip.protection.adaptive_rr_portfolio import AdaptiveRRProtectionPlanner


class FakeMT5:
    def symbol_info(self, _symbol):
        return SimpleNamespace(trade_tick_size=0.01, trade_tick_value_loss=1.0, trade_tick_value=1.0)


def test_atr_authority_is_explicit_and_not_fixed_3000():
    plan = AdaptiveRRProtectionPlanner().plan_portfolio(
        action="BUY", entry_price=2400.0, unit_count=1, profile_id="P1",
        confidence=99.0,
        snapshot={"atr_points": 120.0}, research={}, regime="TREND", point_size=0.01,
    )
    assert plan["status"] == "PLANNED"
    assert plan["stop_basis"] == "ATR_VOLATILITY"
    unit = plan["unit_plans"][0]
    assert unit["stop_loss_points"] == 180.0
    assert unit["take_profit_points"] == 720.0
    assert unit["rr_target"] == 4.0
    assert unit["stop_loss_points"] != 3000.0


def test_validated_research_has_priority_over_atr():
    plan = AdaptiveRRProtectionPlanner().plan_portfolio(
        action="SELL", entry_price=2400.0, unit_count=1, profile_id="P1",
        confidence=99.0,
        snapshot={"atr_points": 120.0},
        research={"validated": True, "sample_size": 120, "recommended_stop_points": 210,
                  "validated_rr_targets": [1.2, 2.2, 3.5]},
        regime="TREND", point_size=0.01,
    )
    assert plan["stop_basis"] == "VALIDATED_RESEARCH"
    assert plan["research_evidence_sufficient"] is True
    assert plan["unit_plans"][0]["stop_loss_points"] == 210.0
    assert plan["unit_plans"][0]["take_profit_points"] == 735.0


def test_financials_are_calculated_per_order_and_total():
    requests = [
        {"symbol": "GOLD#", "price": 2400.0, "sl": 2398.0, "tp": 2404.0, "volume": 0.01},
        {"symbol": "GOLD#", "price": 2400.0, "sl": 2398.0, "tp": 2406.0, "volume": 0.01},
    ]
    plans = (
        {"role": "RR_NEAR", "research_basis": "ATR_VOLATILITY"},
        {"role": "RR_RUNNER", "research_basis": "ATR_VOLATILITY"},
    )
    result = DemoExecutionGateway._protection_financials(
        FakeMT5(), requests, 0.01, plans,
        sl_authority="ATR_VOLATILITY", tp_authority="REGIME_ADAPTIVE_RR_TARGETS",
    )
    assert result["stop_loss_usd_per_order"] == (2.0, 2.0)
    assert result["take_profit_usd_per_order"] == (4.0, 6.0)
    assert result["total_stop_loss_usd"] == 4.0
    assert result["total_take_profit_usd"] == 10.0
    assert result["aggregate_risk_reward_ratio"] == 2.5
    assert result["protection_order_details"][0]["risk_reward_ratio"] == 2.0
    assert result["protection_order_details"][1]["risk_reward_ratio"] == 3.0


def test_missing_tick_metadata_fails_truthfully_without_usd_guess():
    class NoTickMT5:
        def symbol_info(self, _symbol):
            return SimpleNamespace(trade_tick_size=0.0, trade_tick_value_loss=0.0, trade_tick_value=0.0)
    result = DemoExecutionGateway._protection_financials(
        NoTickMT5(), [{"symbol":"GOLD#","price":2400,"sl":2398,"tp":2404,"volume":0.01}], 0.0
    )
    assert result["stop_loss_usd_per_order"] == (None,)
    assert result["take_profit_usd_per_order"] == (None,)
    assert result["total_stop_loss_usd"] is None
    assert result["total_take_profit_usd"] is None


def test_sell_direction_financial_distances_are_absolute():
    result = DemoExecutionGateway._protection_financials(
        FakeMT5(), [{"symbol":"GOLD#","price":2400,"sl":2403,"tp":2394,"volume":0.01}], 0.01
    )
    detail = result["protection_order_details"][0]
    assert detail["sl_points"] == 300.0
    assert detail["tp_points"] == 600.0
    assert detail["risk_usd"] == 3.0
    assert detail["reward_usd"] == 6.0
    assert detail["risk_reward_ratio"] == 2.0
