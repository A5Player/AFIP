from dataclasses import FrozenInstanceError
import pytest
from afip.production_certification_final import ProductionCertificationRuntime

PASS_FIELDS = {
    "1": "regression_audit_passed",
    "2": "duplicate_code_audit_passed",
    "3": "dead_code_audit_passed",
    "4": "architecture_audit_passed",
    "5": "repository_cleanup_passed",
    "6": "safety_audit_passed",
    "7": "security_audit_passed",
    "8": "data_integrity_audit_passed",
    "9": "performance_audit_passed",
}
REASONS = {
    "1": "REGRESSION_AUDIT_PASSED",
    "2": "DUPLICATE_CODE_AUDIT_PASSED",
    "3": "DEAD_CODE_AUDIT_PASSED",
    "4": "ARCHITECTURE_AUDIT_PASSED",
    "5": "REPOSITORY_CLEANUP_PASSED",
    "6": "SAFETY_AUDIT_PASSED",
    "7": "SECURITY_AUDIT_PASSED",
    "8": "DATA_INTEGRITY_AUDIT_PASSED",
    "9": "PERFORMANCE_AUDIT_PASSED",
}


def report(pack: str, **overrides):
    row = {
        "audit_id": f"R{pack}-1234567890ABCDEF",
        "status": "PASS",
        "reason": REASONS[pack],
        "milestone": "R",
        "pack": pack,
        "audit_timestamp": 100 + int(pack),
        PASS_FIELDS[pack]: True,
        "accepted_exception_count": 0,
        "critical_failure_count": 0,
        "broker": "XM",
        "symbol": "GOLD#",
        "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "direct_execution": False,
        "live_execution_enabled": False,
        "order_status": "NO_ORDER_SENT",
    }
    row.update(overrides)
    return row


def reports():
    return [report(str(pack)) for pack in range(1, 10)]


def test_certification_granted_but_execution_stays_locked():
    result = ProductionCertificationRuntime().certify(reports(), certification_timestamp=200)
    assert result.status == "CERTIFIED"
    assert result.production_certification_granted is True
    assert result.release_candidate_granted is False
    assert result.version_1_final_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.next_stage == "R_RELEASE_CANDIDATE"


def test_deterministic_and_immutable():
    runtime = ProductionCertificationRuntime()
    first = runtime.certify(reports(), certification_timestamp=200)
    second = runtime.certify(reports(), certification_timestamp=200)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_missing_required_audit_blocks():
    result = ProductionCertificationRuntime().certify(reports()[:-1], certification_timestamp=200)
    assert "required_production_audit_missing" in result.block_reasons
    assert result.production_certification_granted is False


def test_duplicate_and_future_audit_blocks():
    rows = reports()
    rows[1]["audit_id"] = rows[0]["audit_id"]
    rows[2]["audit_timestamp"] = 300
    result = ProductionCertificationRuntime().certify(rows, certification_timestamp=200)
    assert "duplicate_or_invalid_production_audit_id" in result.block_reasons
    assert "production_certification_chronology_invalid" in result.block_reasons


def test_failed_or_invalid_schema_blocks():
    rows = reports()
    rows[3]["status"] = "BLOCKED"
    rows[4]["reason"] = "WRONG"
    result = ProductionCertificationRuntime().certify(rows, certification_timestamp=200)
    assert "production_audit_not_passed" in result.block_reasons
    assert "production_audit_schema_invalid" in result.block_reasons


def test_critical_block_and_score_threshold():
    rows = reports()
    rows[5]["critical_failure_count"] = 1
    rows[6][PASS_FIELDS["7"]] = False
    result = ProductionCertificationRuntime().certify(rows, certification_timestamp=200, minimum_certification_score=1.0)
    assert "critical_production_audit_block_present" in result.block_reasons
    assert "production_certification_score_below_threshold" in result.block_reasons


def test_policy_violation_blocks_unlock_attempt():
    rows = reports()
    rows[8]["execution_unlock_authorized"] = True
    result = ProductionCertificationRuntime().certify(rows, certification_timestamp=200)
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"


def test_as_dict_preserves_certification_boundaries():
    result = ProductionCertificationRuntime().certify(reports(), certification_timestamp=200)
    data = result.as_dict()
    assert data["production_certification_granted"] is True
    assert data["release_candidate_granted"] is False
    assert data["version_1_final_granted"] is False
    assert data["execution_unlock_authorized"] is False
