from dataclasses import replace

import pytest

from afip.complete_trade_plan import (
    CapitalManagementPlan, CompleteTradePlan, CompleteTradePlanCertifier, EntryPlan,
    ExitPlan, FailureRecoveryPlan, MarketSituationPlan, PositionCarePlan,
    TradePlanDashboardContract, TradePlanLifecycleEvent, TradePlanLifecycleRecorder,
)
from afip.historical_replay_research import AppendOnlyResearchDataset


def make_plan(**overrides):
    plan = CompleteTradePlan(
        plan_id="PLAN-P1-001", plan_version="1.0", symbol="GOLD#",
        ranking_id="RANK-001", selected_standard_id="STD-001",
        market=MarketSituationPlan("TREND", "BULL_FLAG", "CONTINUATION", "HH_HL", "NORMAL", "NORMAL", "LONDON", "NORMAL", "BUY", 88.0, ("structure_break",)),
        entry=EntryPlan("BUY", "RETEST", 2300.0, 2302.0, ("close_above_zone",), ("structure_break",), True, 900, 2, 3, 100.0, 35.0, 10.0),
        capital=CapitalManagementPlan("P1", 0.01, 1000.0, 5000.0, 5000.0, 4800.0, 1.0, 1.0, 20.0, 3.0, 6.0, 10.0, 5, 3, 4, 3, 2, 3),
        care=PositionCarePlan("trend continuation remains valid", ("higher_low_intact",), ("higher_low_broken",), "after_1R", "structure_trailing", "target_one_partial", "only_after_protected_profit", 172800, "ALLOW_IF_RISK_VALID", "CLOSE_OR_PROTECT", "NO_ADD_DURING_HIGH_IMPACT"),
        exit=ExitPlan(2290.0, 2288.0, (2310.0, 2320.0), ("structure_reversal",), "maximum_holding_time", "close_on_thesis_failure", "reduce_on_extreme_volatility", "close_if_protection_unavailable", "protect_after_1R", "trail_below_structure"),
        recovery=FailureRecoveryPlan("BLOCK_NEW_RISK", "RECONNECT_AND_RECONCILE", "BLOCK_NEW_RISK", True, "SAFE_MODE_AND_RECONCILE", "RESTORE_CHECKPOINT_OR_SAFE_MODE", "BLOCK_NEW_RISK", "RETRY_WITH_LIMIT", "STOP_AUTOMATION_AND_RECONCILE", "ENTER_SAFE_MODE", "BLOCK_NEW_RISK_AND_PROTECT_OPEN_POSITIONS", True),
    )
    return replace(plan, **overrides)


def test_complete_plan_certifies_and_caps_units():
    result = CompleteTradePlanCertifier().certify(make_plan())
    assert result.certified is True
    assert result.allowed_units == 2
    assert result.rule == "NO_COMPLETE_PLAN_NO_ORDER"


def test_capital_capacity_is_minimum_authority():
    plan = make_plan(capital=replace(make_plan().capital, correlation_capacity_units=1))
    result = CompleteTradePlanCertifier().certify(plan)
    assert result.certified is False
    assert "requested_units_above_capital_capacity" in result.rejection_reasons
    assert result.allowed_units == 0


def test_no_capacity_blocks_plan():
    plan = make_plan(capital=replace(make_plan().capital, margin_capacity_units=0))
    result = CompleteTradePlanCertifier().certify(plan)
    assert "capital_capacity_unavailable" in result.rejection_reasons


def test_unknown_market_blocks_plan():
    plan = make_plan(market=replace(make_plan().market, regime="UNKNOWN"))
    assert CompleteTradePlanCertifier().certify(plan).certified is False


def test_incomplete_entry_blocks_plan():
    plan = make_plan(entry=replace(make_plan().entry, confirmation_conditions=()))
    assert "entry_conditions_incomplete" in CompleteTradePlanCertifier().certify(plan).rejection_reasons


def test_missing_stop_blocks_plan():
    plan = make_plan(exit=replace(make_plan().exit, initial_stop_price=0.0))
    assert "protective_stop_missing" in CompleteTradePlanCertifier().certify(plan).rejection_reasons


def test_restart_reconciliation_is_mandatory():
    plan = make_plan(recovery=replace(make_plan().recovery, restart_reconciliation_required=False))
    assert "restart_reconciliation_not_required" in CompleteTradePlanCertifier().certify(plan).rejection_reasons


def test_drawdown_limit_blocks_plan():
    plan = make_plan(capital=replace(make_plan().capital, current_floating_drawdown_percent=21.0))
    assert "account_drawdown_limit_reached" in CompleteTradePlanCertifier().certify(plan).rejection_reasons


def test_dataset_records_plan_and_certification(tmp_path):
    result = CompleteTradePlanCertifier(tmp_path).certify(make_plan())
    dataset = AppendOnlyResearchDataset(tmp_path)
    assert result.certified
    assert dataset.count("complete_trade_plans") == 1
    assert dataset.count("trade_plan_certifications") == 1


def test_lifecycle_recorder_is_append_only(tmp_path):
    recorder = TradePlanLifecycleRecorder(tmp_path)
    event = TradePlanLifecycleEvent("E1", "PLAN-P1-001", "P1", "POSITION_HELD", "thesis_valid", "Higher-low structure remains intact.", "2026-07-19T00:00:00+00:00", {"stop": 2290.0})
    recorder.record(event)
    assert AppendOnlyResearchDataset(tmp_path).count("trade_plan_lifecycle_events") == 1


def test_unknown_lifecycle_event_rejected(tmp_path):
    recorder = TradePlanLifecycleRecorder(tmp_path)
    event = TradePlanLifecycleEvent("E1", "P", "P1", "INVALID", "x", "x", "2026-07-19T00:00:00+00:00", {})
    with pytest.raises(ValueError):
        recorder.record(event)


def test_dashboard_contract_is_two_page_safe():
    contract = TradePlanDashboardContract.as_dict()
    assert contract["operations_profiles"] == ("P1", "P2", "P3", "P4")
    assert contract["operations_refresh_seconds"] == 5
    assert contract["intelligence_refresh"] == "MANUAL_ONLY"
    assert contract["intelligence_preserve_scroll_position"] is True


def test_plan_checksum_is_deterministic():
    plan = make_plan()
    assert plan.as_dict()["plan_checksum"] == plan.as_dict()["plan_checksum"]


def test_warning_does_not_bypass_hard_gates():
    plan = make_plan(entry=replace(make_plan().entry, chase_prohibited=False))
    result = CompleteTradePlanCertifier().certify(plan)
    assert result.certified
    assert "entry_chase_prohibition_not_enabled" in result.warnings


def test_direction_must_be_trade_direction():
    plan = make_plan(entry=replace(make_plan().entry, direction="FLAT"))
    assert "entry_direction_invalid" in CompleteTradePlanCertifier().certify(plan).rejection_reasons


def test_requested_units_cannot_exceed_plan_maximum():
    plan = make_plan(entry=replace(make_plan().entry, requested_units=4, maximum_units=3))
    assert "requested_units_above_plan_maximum" in CompleteTradePlanCertifier().certify(plan).rejection_reasons
