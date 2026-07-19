from __future__ import annotations

from dataclasses import replace

from afip.complete_trade_plan import (
    CapitalManagementPlan, CompleteTradePlan, EntryPlan, ExitPlan,
    FailureRecoveryPlan, MarketSituationPlan, PositionCarePlan,
)
from afip.position_care_runtime import (
    PositionCareDashboardContract, PositionCareDashboardReadModelBuilder,
    PositionCareSnapshot, PositionCareSupervisor,
)


def plan() -> CompleteTradePlan:
    return CompleteTradePlan(
        plan_id="PLAN-13", plan_version="1", symbol="GOLD#", ranking_id="R1", selected_standard_id="S1",
        market=MarketSituationPlan("TREND","P","F","BULL","NORMAL","READY","LONDON","CLEAR","BUY",90,("invalid",)),
        entry=EntryPlan("BUY","RETEST",100,101,("confirm",),("cancel",),True,300,1,3,10,35,5),
        capital=CapitalManagementPlan(profile_id="P1", base_lot=0.01, capital_per_unit=1000, account_balance=5000, account_equity=5000, free_margin=4000, current_floating_drawdown_percent=0, maximum_trade_risk_percent=1, maximum_account_drawdown_percent=10, daily_loss_limit_percent=2, weekly_loss_limit_percent=4, monthly_loss_limit_percent=6, capital_capacity_units=3, risk_capacity_units=3, margin_capacity_units=3, exposure_capacity_units=3, correlation_capacity_units=3, profile_capacity_units=3),
        care=PositionCarePlan("trend intact",("valid",),("failed",),"plus 100","structure trail","half at target","no add",3600,"allowed","close","reduce"),
        exit=ExitPlan(95,94,(110,), ("break",),"time","thesis","volatility","emergency","protect","trail"),
        recovery=FailureRecoveryPlan("wait","wait","wait",True,"reconcile","safe","wait","retry","pause","safe","safe",True),
    )


def snap(**changes) -> PositionCareSnapshot:
    base = PositionCareSnapshot(
        "S1","PLAN-13","P1","GOLD#","123","BUY",100,105,95,98,110,0.01,50,500,20,600,
        True,True,True,True,True,True,True,True,False,False,False,False,False,False,"2026-07-19T00:00:00+00:00"
    )
    return replace(base, **changes)


def test_hold_position():
    d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap())
    assert d.recommended_action == "HOLD_POSITION" and not d.execution_permission


def test_break_even():
    d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(break_even_triggered=True))
    assert d.recommended_action == "RECOMMEND_BREAK_EVEN_UPDATE" and d.proposed_stop_price == 100


def test_trailing_precedes_break_even():
    d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(break_even_triggered=True,trailing_triggered=True))
    assert d.recommended_action == "RECOMMEND_TRAILING_STOP_UPDATE"


def test_partial_close_precedes_trailing():
    d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(partial_close_triggered=True,trailing_triggered=True))
    assert d.recommended_action == "RECOMMEND_PARTIAL_CLOSE" and d.proposed_close_fraction == .5


def test_target_close():
    assert PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(target_reached=True)).recommended_action == "RECOMMEND_FULL_CLOSE"


def test_thesis_failure_close():
    assert "holding_thesis_failed" in PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(thesis_valid=False)).reason_codes


def test_structure_failure_close():
    assert PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(structure_valid=False)).proposed_close_fraction == 1


def test_hard_invalidation_close():
    assert "hard_invalidation_reached" in PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(hard_invalidation_reached=True)).reason_codes


def test_emergency_has_priority():
    d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(emergency_condition_active=True,target_reached=True))
    assert d.reason_codes == ("emergency_exit_condition_active",)


def test_holding_timeout():
    assert "maximum_holding_time_reached" in PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(holding_seconds=3600)).reason_codes


def test_market_quality_caution():
    assert PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(volatility_acceptable=False)).recommended_action == "HOLD_WITH_CAUTION"


def test_identity_mismatch_safe_mode():
    d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(profile_id="P2"))
    assert d.status == "BLOCKED" and d.recommended_action == "ENTER_SAFE_MODE"


def test_stale_data_safe_mode():
    assert PositionCareSupervisor().evaluate(plan=plan(), snapshot=snap(market_data_fresh=False)).recommended_action == "ENTER_SAFE_MODE"


def test_dataset_append(tmp_path):
    PositionCareSupervisor(tmp_path).evaluate(plan=plan(), snapshot=snap())
    assert (tmp_path / "position_care_snapshots.jsonl").exists()
    assert (tmp_path / "position_care_decisions.jsonl").exists()


def test_dashboard_read_model():
    s=snap(); d=PositionCareSupervisor().evaluate(plan=plan(), snapshot=s)
    r=PositionCareDashboardReadModelBuilder().build(snapshot=s, decision=d)
    assert r["execution_permission"] is False and r["holding_reason"] == "trend intact"


def test_dashboard_contract():
    c=PositionCareDashboardContract.as_dict()
    assert c["operations_refresh_seconds"] == 5 and c["execution_permission_locked_false"] is True
