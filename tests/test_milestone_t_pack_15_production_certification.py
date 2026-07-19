from __future__ import annotations
from dataclasses import replace
from afip.milestone_t_certification import (
    MilestoneTClosureContract, MilestoneTEvidenceSnapshot,
    MilestoneTFinalHandoffBuilder, MilestoneTProductionCertifier,
)


def evidence(**changes):
    base = MilestoneTEvidenceSnapshot(
        "EV1", "COMMIT", True, True, True, True, True, True, True, True,
        True, True, True, True, True, True, True, True, True, True,
        "2026-07-19T00:00:00+00:00",
    )
    return replace(base, **changes)


def certify(**changes):
    return MilestoneTProductionCertifier().certify(evidence(**changes))


def test_complete_evidence_certifies_milestone():
    c=certify(); assert c.certification_status == "PASS" and c.milestone_status == "MILESTONE_T_CERTIFIED"


def test_execution_permission_remains_false():
    assert certify().execution_permission is False


def test_financial_naming_required():
    assert "financial_naming_not_passed" in certify(financial_naming_passed=False).reason_codes


def test_full_regression_required():
    assert "full_regression_not_passed" in certify(full_regression_passed=False).reason_codes


def test_local_quality_required():
    assert "local_quality_not_passed" in certify(local_quality_passed=False).reason_codes


def test_complete_trade_plan_required():
    assert "complete_trade_plan_unavailable" in certify(complete_trade_plan_available=False).reason_codes


def test_trade_plan_runtime_required():
    assert "trade_plan_runtime_unavailable" in certify(trade_plan_runtime_available=False).reason_codes


def test_position_care_required():
    assert "position_care_unavailable" in certify(position_care_available=False).reason_codes


def test_unattended_continuity_required():
    assert "unattended_continuity_unavailable" in certify(unattended_continuity_available=False).reason_codes


def test_dataset_registry_required():
    assert "dataset_registry_incomplete" in certify(dataset_registry_complete=False).reason_codes


def test_documentation_required():
    c=certify(bilingual_documentation_complete=False); assert c.certification_status == "BLOCK"


def test_execution_lock_required():
    assert "execution_permission_not_locked" in certify(execution_permission_locked_false=False).reason_codes


def test_order_authority_must_not_be_added():
    c=certify(mt5_order_send_not_added=False); assert "mt5_order_send_authority_detected" in c.reason_codes


def test_all_failures_are_reported():
    c=certify(financial_naming_passed=False, full_regression_passed=False)
    assert len(c.reason_codes) == 2


def test_dataset_and_handoff(tmp_path):
    s=MilestoneTProductionCertifier(tmp_path); c=s.certify(evidence())
    h=MilestoneTFinalHandoffBuilder().build(c)
    assert (tmp_path/"milestone_t_certification_evidence.jsonl").exists()
    assert (tmp_path/"milestone_t_closure_certifications.jsonl").exists()
    assert h["next_milestone_entry_allowed"] is True and h["execution_permission"] is False


def test_closure_contract_is_locked():
    c=MilestoneTClosureContract.as_dict()
    assert c["required_packs"] == (11,12,13,14,15) and c["execution_permission_locked_false"]
