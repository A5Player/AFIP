from dataclasses import replace

from afip.complete_trade_plan import (
    CapitalManagementPlan, CompleteTradePlan, CompleteTradePlanCertifier, EntryPlan,
    ExitPlan, FailureRecoveryPlan, MarketSituationPlan, PositionCarePlan,
)
from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.trade_plan_runtime import (
    CapitalCapacitySnapshot, CertifiedTradePlanRuntimeCoordinator,
    ProfileOperationsReadModelBuilder, RecoveryReconciliationSnapshot,
    TradePlanRuntimeDashboardContract,
)


def make_plan():
    return CompleteTradePlan(
        plan_id="PLAN-P1-001", plan_version="1.0", symbol="GOLD#", ranking_id="RANK-001", selected_standard_id="STD-001",
        market=MarketSituationPlan("TREND", "BULL_FLAG", "CONTINUATION", "HH_HL", "NORMAL", "NORMAL", "LONDON", "NORMAL", "BUY", 88.0, ("structure_break",)),
        entry=EntryPlan("BUY", "RETEST", 2300.0, 2302.0, ("close_above_zone",), ("structure_break",), True, 900, 2, 3, 100.0, 35.0, 10.0),
        capital=CapitalManagementPlan("P1", 0.01, 1000.0, 5000.0, 5000.0, 4800.0, 1.0, 1.0, 20.0, 3.0, 6.0, 10.0, 5, 3, 4, 3, 2, 3),
        care=PositionCarePlan("trend continuation remains valid", ("higher_low_intact",), ("higher_low_broken",), "after_1R", "structure_trailing", "target_one_partial", "only_after_protected_profit", 172800, "ALLOW_IF_RISK_VALID", "CLOSE_OR_PROTECT", "NO_ADD_DURING_HIGH_IMPACT"),
        exit=ExitPlan(2290.0, 2288.0, (2310.0, 2320.0), ("structure_reversal",), "maximum_holding_time", "close_on_thesis_failure", "reduce_on_extreme_volatility", "close_if_protection_unavailable", "protect_after_1R", "trail_below_structure"),
        recovery=FailureRecoveryPlan("BLOCK_NEW_RISK", "RECONNECT_AND_RECONCILE", "BLOCK_NEW_RISK", True, "SAFE_MODE_AND_RECONCILE", "RESTORE_CHECKPOINT_OR_SAFE_MODE", "BLOCK_NEW_RISK", "RETRY_WITH_LIMIT", "STOP_AUTOMATION_AND_RECONCILE", "ENTER_SAFE_MODE", "BLOCK_NEW_RISK_AND_PROTECT_OPEN_POSITIONS", True),
    )


def make_cap(**changes):
    base = CapitalCapacitySnapshot("CAP-1", "P1", "GOLD#", 5000, 5000, 4800, 1, 2, 3, 5, 3, 4, 3, 2, 3, "2026-07-19T00:00:00+00:00")
    return replace(base, **changes)


def make_rec(**changes):
    base = RecoveryReconciliationSnapshot("REC-1", "P1", True, True, True, True, True, True, False, True, True, False, "2026-07-19T00:00:00+00:00")
    return replace(base, **changes)


def decide(**changes):
    plan = changes.pop("plan", make_plan())
    cert = changes.pop("certification", CompleteTradePlanCertifier().certify(plan))
    return CertifiedTradePlanRuntimeCoordinator().decide(plan=plan, certification=cert, capital_snapshot=changes.pop("capital_snapshot", make_cap()), reconciliation=changes.pop("reconciliation", make_rec()), ranking_eligible=changes.pop("ranking_eligible", True))


def test_capital_snapshot_uses_lowest_capacity():
    assert make_cap().allowed_units == 2


def test_runtime_ready_but_execution_permission_false():
    result = decide()
    assert result.status == "READY_FOR_EXECUTION_GATE_REVIEW"
    assert result.allowed_units == 2
    assert result.execution_permission is False


def test_ineligible_ranking_blocks():
    assert "ranking_not_eligible" in decide(ranking_eligible=False).reason_codes


def test_uncertified_plan_blocks():
    plan = replace(make_plan(), market=replace(make_plan().market, regime="UNKNOWN"))
    assert decide(plan=plan).status == "BLOCKED"


def test_runtime_capacity_drop_blocks():
    result = decide(capital_snapshot=make_cap(correlation_capacity_units=1))
    assert "runtime_capacity_below_certified_units" in result.reason_codes
    assert result.allowed_units == 0


def test_mt5_disconnect_blocks():
    assert "mt5_not_connected" in decide(reconciliation=make_rec(mt5_connected=False)).reason_codes


def test_stale_data_blocks():
    assert "market_data_stale" in decide(reconciliation=make_rec(market_data_fresh=False)).reason_codes


def test_unknown_orders_block():
    assert "unknown_orders_present" in decide(reconciliation=make_rec(unknown_orders_present=True)).reason_codes


def test_manual_order_guard_blocks():
    assert "manual_order_guard_active" in decide(reconciliation=make_rec(manual_order_guard_clear=False)).reason_codes


def test_safe_mode_blocks():
    assert "safe_mode_active" in decide(reconciliation=make_rec(safe_mode_active=True)).reason_codes


def test_profile_mismatch_blocks():
    assert "capital_snapshot_profile_mismatch" in decide(capital_snapshot=make_cap(profile_id="P2")).reason_codes


def test_symbol_mismatch_blocks():
    assert "capital_snapshot_symbol_mismatch" in decide(capital_snapshot=make_cap(symbol="XAUUSD")).reason_codes


def test_append_only_runtime_datasets(tmp_path):
    plan = make_plan(); cert = CompleteTradePlanCertifier().certify(plan)
    CertifiedTradePlanRuntimeCoordinator(tmp_path).decide(plan=plan, certification=cert, capital_snapshot=make_cap(), reconciliation=make_rec(), ranking_eligible=True)
    ds = AppendOnlyResearchDataset(tmp_path)
    assert ds.count("capital_capacity_snapshots") == 1
    assert ds.count("recovery_reconciliations") == 1
    assert ds.count("certified_plan_runtime_decisions") == 1


def test_operations_read_model_contains_trace_chain():
    plan = make_plan(); cert = CompleteTradePlanCertifier().certify(plan); decision = decide()
    model = ProfileOperationsReadModelBuilder().build(plan=plan, certification=cert, capital_snapshot=make_cap(), reconciliation=make_rec(), decision=decision)
    assert model["ranking_id"] == "RANK-001"
    assert model["runtime_allowed_units"] == 2
    assert model["execution_permission"] is False


def test_dashboard_contract_preserves_manual_intelligence_scroll():
    contract = TradePlanRuntimeDashboardContract.as_dict()
    assert contract["operations_profiles"] == ("P1", "P2", "P3", "P4")
    assert contract["operations_refresh_seconds"] == 5
    assert contract["intelligence_refresh"] == "MANUAL_ONLY"
    assert contract["intelligence_preserve_scroll_position"] is True


def test_decision_checksum_is_deterministic_per_payload_shape():
    result = decide().as_dict()
    assert len(result["decision_checksum"]) == 64
