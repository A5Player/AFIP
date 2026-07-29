from __future__ import annotations

from dataclasses import replace

from afip.complete_trade_plan import (
    CapitalManagementPlan,
    CompleteTradePlan,
    EntryPlan,
    ExitPlan,
    FailureRecoveryPlan,
    MarketSituationPlan,
    PositionCarePlan,
)
from afip.position_care_runtime import (
    PositionCareDashboardReadModelBuilder,
    PositionCareSnapshot,
    PositionCareSupervisor,
)


def _plan() -> CompleteTradePlan:
    return CompleteTradePlan(
        plan_id="PLAN-LIFECYCLE-1", plan_version="1", symbol="GOLD#",
        ranking_id="RANK-1", selected_standard_id="STANDARD-1",
        market=MarketSituationPlan("TREND", "P", "F", "BULL", "NORMAL", "READY", "LONDON", "CLEAR", "BUY", 95, ("invalid",)),
        entry=EntryPlan("BUY", "RETEST", 2400, 2401, ("confirm",), ("cancel",), True, 200, 1, 3, 10, 35, 5),
        capital=CapitalManagementPlan(
            profile_id="P1", base_lot=0.01, capital_per_unit=1000,
            account_balance=5000, account_equity=5000, free_margin=4000,
            current_floating_drawdown_percent=0, maximum_trade_risk_percent=1,
            maximum_account_drawdown_percent=10, daily_loss_limit_percent=2,
            weekly_loss_limit_percent=4, monthly_loss_limit_percent=6,
            capital_capacity_units=3, risk_capacity_units=3, margin_capacity_units=3,
            exposure_capacity_units=3, correlation_capacity_units=3, profile_capacity_units=3,
        ),
        care=PositionCarePlan("trend intact", ("valid",), ("failed",), "plus 100", "structure trail", "half at target", "no add", 3600, "allowed", "close", "reduce"),
        exit=ExitPlan(2398, 2397, (2404,), ("break",), "time", "thesis", "volatility", "emergency", "protect", "trail"),
        recovery=FailureRecoveryPlan("wait", "wait", "wait", True, "reconcile", "safe", "wait", "retry", "pause", "safe", "safe", True),
    )


def _snapshot(**changes) -> PositionCareSnapshot:
    base = PositionCareSnapshot(
        "SNAP-1", "PLAN-LIFECYCLE-1", "P1", "GOLD#", "123", "BUY",
        2400.0, 2402.0, 2398.0, 2399.0, 2404.0, 0.01, 2.0,
        250.0, 80.0, 600, True, True, True, True, True, True, True, True,
        False, False, False, False, False, False, "2026-07-29T00:00:00+00:00",
    )
    return replace(base, **changes)


def _build(snapshot: PositionCareSnapshot):
    decision = PositionCareSupervisor().evaluate(plan=_plan(), snapshot=snapshot)
    return PositionCareDashboardReadModelBuilder().build(
        snapshot=snapshot,
        decision=decision,
        point_size=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
    )


def test_remaining_risk_and_excursions_are_financially_explainable():
    record = _build(_snapshot())
    assert record["lifecycle_financial_status"] == "AVAILABLE"
    assert record["initial_risk_points"] == 200.0
    assert record["initial_risk_usd"] == 2.0
    assert record["remaining_risk_points"] == 100.0
    assert record["remaining_risk_usd"] == 1.0
    assert record["locked_profit_usd"] == 0.0
    assert record["maximum_favorable_excursion_usd"] == 2.5
    assert record["maximum_adverse_excursion_usd"] == 0.8
    assert record["unrealized_profit_usd"] == 2.0
    assert record["execution_permission"] is False


def test_stop_above_entry_is_locked_profit_not_remaining_risk():
    record = _build(_snapshot(current_stop_price=2401.0))
    assert record["remaining_risk_usd"] == 0.0
    assert record["locked_profit_points"] == 100.0
    assert record["locked_profit_usd"] == 1.0


def test_proposed_break_even_removes_risk_without_claiming_profit():
    snapshot = _snapshot(break_even_triggered=True)
    decision = PositionCareSupervisor().evaluate(plan=_plan(), snapshot=snapshot)
    record = PositionCareDashboardReadModelBuilder().build(
        snapshot=snapshot, decision=decision, point_size=0.01,
        trade_tick_size=0.01, trade_tick_value=1.0,
    )
    assert decision.recommended_action == "RECOMMEND_BREAK_EVEN_UPDATE"
    assert record["proposed_remaining_risk_usd"] == 0.0
    assert record["proposed_locked_profit_usd"] == 0.0


def test_missing_broker_metadata_never_guesses_usd():
    snapshot = _snapshot()
    decision = PositionCareSupervisor().evaluate(plan=_plan(), snapshot=snapshot)
    record = PositionCareDashboardReadModelBuilder().build(snapshot=snapshot, decision=decision)
    assert record["lifecycle_financial_status"] == "BROKER_METADATA_UNAVAILABLE"
    assert record["initial_risk_usd"] is None
    assert record["remaining_risk_usd"] is None
    assert record["maximum_favorable_excursion_usd"] is None


def test_sell_direction_uses_correct_risk_and_locked_profit_domains():
    sell_snapshot = _snapshot(
        direction="SELL", entry_price=2400.0, current_price=2398.0,
        initial_stop_price=2402.0, current_stop_price=2399.0,
        current_take_profit_price=2396.0,
    )
    sell_plan = replace(_plan(), entry=replace(_plan().entry, direction="SELL"))
    decision = PositionCareSupervisor().evaluate(plan=sell_plan, snapshot=sell_snapshot)
    record = PositionCareDashboardReadModelBuilder().build(
        snapshot=sell_snapshot, decision=decision, point_size=0.01,
        trade_tick_size=0.01, trade_tick_value=1.0,
    )
    assert record["initial_risk_usd"] == 2.0
    assert record["remaining_risk_usd"] == 0.0
    assert record["locked_profit_usd"] == 1.0
    assert record["current_distance_to_target_usd"] == 2.0


def test_dashboard_source_exposes_lifecycle_financial_truth():
    from pathlib import Path
    source = Path("afip/dashboard_ui/split_runtime.py").read_text(encoding="utf-8")
    for label in (
        "Initial risk USD", "Remaining risk USD", "Locked profit USD",
        "Unrealized P/L USD", "MFE points / USD", "MAE points / USD",
        "Distance to TP points / USD", "Exit recommendation", "Exit reason",
    ):
        assert label in source
