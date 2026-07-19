from __future__ import annotations
from dataclasses import replace
from afip.unattended_continuity import (
    ContinuityDashboardReadModelBuilder, RuntimeContinuityCheckpoint,
    UnattendedContinuityContract, UnattendedContinuitySupervisor,
)


def checkpoint(**changes):
    base = RuntimeContinuityCheckpoint(
        "CP1","RUN2","RUN1","P1","GOLD#","2026-07-19T00:00:00+00:00",
        "2026-07-19T00:00:05+00:00",False,0,True,True,True,True,True,
        1,1,0,0,0,False,True,True,True,True,False,"2026-07-19T00:00:05+00:00"
    )
    return replace(base, **changes)


def evaluate(**changes):
    return UnattendedContinuitySupervisor().evaluate(checkpoint(**changes))


def test_continuity_ready():
    d=evaluate(); assert d.recommended_action == "CONTINUE_SUPERVISION" and d.new_risk_allowed


def test_restart_reconciled():
    d=evaluate(restart_detected=True); assert d.recommended_action == "RESUME_SUPERVISION_AFTER_RESTART"


def test_interruption_reconciled():
    assert evaluate(interruption_seconds=30).recommended_action == "RESUME_SUPERVISION_AFTER_INTERRUPTION"


def test_mt5_disconnect_waits():
    d=evaluate(mt5_connected=False); assert d.recommended_action == "PAUSE_AND_RECONNECT" and d.reconciliation_required


def test_internet_disconnect_waits():
    assert "internet_connection_unavailable" in evaluate(internet_connected=False).reason_codes


def test_stale_data_waits():
    assert evaluate(market_data_fresh=False).recommended_action == "PAUSE_AND_REFRESH_STATE"


def test_manual_position_safe_mode():
    d=evaluate(manual_position_detected=True); assert d.recommended_action == "ENTER_SAFE_MODE" and d.operator_attention_required


def test_unknown_position_blocks():
    assert "unknown_positions_present" in evaluate(unknown_position_count=1).reason_codes


def test_missing_position_blocks():
    assert "ledger_positions_missing_from_account" in evaluate(missing_position_count=1).reason_codes


def test_count_mismatch_reconciles():
    d=evaluate(open_position_count=2); assert d.recommended_action == "RECONCILE_POSITIONS" and not d.position_care_allowed


def test_pending_changes_reconcile():
    assert evaluate(pending_change_count=1).recommended_action == "RECONCILE_PENDING_CHANGES"


def test_drawdown_enters_safe_mode():
    assert "drawdown_limit_exceeded" in evaluate(drawdown_within_limit=False).reason_codes


def test_invalid_chain_has_high_priority():
    d=evaluate(append_only_chain_valid=False, mt5_connected=False); assert d.reason_codes == ("append_only_chain_invalid",)


def test_duplicate_prevention_pauses_new_risk():
    d=evaluate(duplicate_prevention_ready=False); assert d.recommended_action == "PAUSE_NEW_RISK" and not d.new_risk_allowed


def test_dataset_and_dashboard(tmp_path):
    c=checkpoint(); s=UnattendedContinuitySupervisor(tmp_path); d=s.evaluate(c)
    r=ContinuityDashboardReadModelBuilder().build(checkpoint=c, decision=d)
    assert (tmp_path/"runtime_continuity_checkpoints.jsonl").exists()
    assert (tmp_path/"runtime_recovery_decisions.jsonl").exists()
    assert r["execution_permission"] is False


def test_contract_execution_locked():
    c=UnattendedContinuityContract.as_dict(); assert c["restart_requires_reconciliation"] and c["execution_permission_locked_false"]
