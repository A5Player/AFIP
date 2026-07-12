from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from afip.production_duplicate_code_audit import ProductionDuplicateCodeAuditRuntime


def _regression(**overrides):
    payload = {
        "audit_id": "RAUD-1234567890ABCDEF", "status": "PASS", "milestone": "R", "pack": "1",
        "regression_audit_passed": True, "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT", "direct_execution": False,
        "live_execution_enabled": False, "production_certification_granted": False, "release_candidate_granted": False,
    }
    payload.update(overrides)
    return payload


def _policy():
    return {"broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
            "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT",
            "direct_execution": False, "live_execution_enabled": False,
            "production_certification_granted": False, "release_candidate_granted": False}


def _fingerprint(value):
    return sha256(value.encode()).hexdigest()


def _findings():
    return [
        {"finding_id": "DUP-001", "timestamp": 1000, "duplicate_kind": "EXACT", "severity": "LOW",
         "fingerprint": _fingerprint("a"), "occurrence_count": 2, "duplicated_line_count": 10,
         "expected_duplicate": False, "review_status": "REMEDIATION_REQUIRED", **_policy()},
        {"finding_id": "DUP-002", "timestamp": 1001, "duplicate_kind": "STRUCTURAL", "severity": "MEDIUM",
         "fingerprint": _fingerprint("b"), "occurrence_count": 3, "duplicated_line_count": 20,
         "expected_duplicate": False, "review_status": "REMEDIATION_REQUIRED", **_policy()},
        {"finding_id": "DUP-003", "timestamp": 1002, "duplicate_kind": "EXPECTED", "severity": "INFO",
         "fingerprint": _fingerprint("c"), "occurrence_count": 4, "duplicated_line_count": 30,
         "expected_duplicate": True, "review_status": "ACCEPTED", **_policy()},
    ]


def test_duplicate_code_audit_passes_deterministically():
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(), _findings(), audit_timestamp=2000, scanned_line_count=10000,
    )
    assert result.status == "PASS"
    assert result.duplicate_code_audit_passed is True
    assert result.actionable_duplicate_count == 2
    assert result.duplicated_line_count == 30
    assert result.duplicate_ratio == 0.003
    assert result.next_audit == "R_DEAD_CODE_AUDIT"


def test_report_is_immutable_and_repeatable():
    runtime = ProductionDuplicateCodeAuditRuntime()
    first = runtime.audit(_regression(), _findings(), audit_timestamp=2000, scanned_line_count=10000)
    second = runtime.audit(_regression(), _findings(), audit_timestamp=2000, scanned_line_count=10000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_regression_lineage():
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(pack="0", regression_audit_passed=False), _findings(), audit_timestamp=2000, scanned_line_count=10000,
    )
    assert "regression_audit_lineage_invalid" in result.block_reasons


def test_blocks_duplicate_ids_and_bad_chronology():
    rows = _findings()
    rows[1]["finding_id"] = rows[0]["finding_id"]
    rows[2]["timestamp"] = 9999
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(), rows, audit_timestamp=2000, scanned_line_count=10000,
    )
    assert "duplicate_or_invalid_duplicate_finding_id" in result.block_reasons
    assert "duplicate_audit_chronology_invalid" in result.block_reasons


def test_blocks_invalid_schema_and_incomplete_review():
    rows = _findings()
    rows[0]["fingerprint"] = "invalid"
    rows[1]["review_status"] = "PENDING"
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(), rows, audit_timestamp=2000, scanned_line_count=10000,
    )
    assert "duplicate_finding_schema_invalid" in result.block_reasons
    assert "duplicate_finding_review_incomplete" in result.block_reasons


def test_blocks_ratio_excess_and_critical_duplicate():
    rows = _findings()
    rows[0]["duplicated_line_count"] = 600
    rows[0]["severity"] = "CRITICAL"
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(), rows, audit_timestamp=2000, scanned_line_count=1000,
    )
    assert "duplicate_ratio_exceeds_limit_or_scan_invalid" in result.block_reasons
    assert "critical_duplicate_code_detected" in result.block_reasons


def test_expected_duplicates_are_not_actionable():
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(), _findings(), audit_timestamp=2000, scanned_line_count=10000,
    )
    assert result.expected_duplicate_count == 1
    assert "DUP-003" not in result.actionable_finding_ids
    assert result.cleanup_required is True


def test_certification_release_cleanup_and_execution_remain_controlled():
    rows = [_findings()[2]]
    result = ProductionDuplicateCodeAuditRuntime().audit(
        _regression(), rows, audit_timestamp=2000, scanned_line_count=10000,
    )
    assert result.cleanup_required is False
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
