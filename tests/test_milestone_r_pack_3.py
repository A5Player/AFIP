from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from afip.production_dead_code_audit import ProductionDeadCodeAuditRuntime


def _duplicate(**overrides):
    payload = {
        "audit_id": "DAUD-1234567890ABCDEF", "status": "PASS", "milestone": "R", "pack": "2",
        "duplicate_code_audit_passed": True, "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
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
        {"finding_id": "DEAD-001", "timestamp": 1000, "dead_code_kind": "UNREACHABLE", "severity": "LOW",
         "fingerprint": _fingerprint("a"), "reference_count": 0, "dead_line_count": 12,
         "retained_by_policy": False, "review_status": "REMEDIATION_REQUIRED", **_policy()},
        {"finding_id": "DEAD-002", "timestamp": 1001, "dead_code_kind": "UNUSED_SYMBOL", "severity": "MEDIUM",
         "fingerprint": _fingerprint("b"), "reference_count": 0, "dead_line_count": 18,
         "retained_by_policy": False, "review_status": "REMEDIATION_REQUIRED", **_policy()},
        {"finding_id": "DEAD-003", "timestamp": 1002, "dead_code_kind": "RETAINED", "severity": "INFO",
         "fingerprint": _fingerprint("c"), "reference_count": 0, "dead_line_count": 25,
         "retained_by_policy": True, "review_status": "ACCEPTED", **_policy()},
    ]


def test_dead_code_audit_passes_deterministically():
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(), _findings(), audit_timestamp=2000, scanned_line_count=10000,
    )
    assert result.status == "PASS"
    assert result.dead_code_audit_passed is True
    assert result.actionable_dead_code_count == 2
    assert result.dead_line_count == 30
    assert result.dead_code_ratio == 0.003
    assert result.next_audit == "R_ARCHITECTURE_AUDIT"


def test_report_is_immutable_and_repeatable():
    runtime = ProductionDeadCodeAuditRuntime()
    first = runtime.audit(_duplicate(), _findings(), audit_timestamp=2000, scanned_line_count=10000)
    second = runtime.audit(_duplicate(), _findings(), audit_timestamp=2000, scanned_line_count=10000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_duplicate_audit_lineage():
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(pack="1", duplicate_code_audit_passed=False), _findings(), audit_timestamp=2000, scanned_line_count=10000,
    )
    assert "duplicate_code_audit_lineage_invalid" in result.block_reasons


def test_blocks_duplicate_ids_and_bad_chronology():
    rows = _findings()
    rows[1]["finding_id"] = rows[0]["finding_id"]
    rows[2]["timestamp"] = 9999
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(), rows, audit_timestamp=2000, scanned_line_count=10000,
    )
    assert "duplicate_or_invalid_dead_code_finding_id" in result.block_reasons
    assert "dead_code_audit_chronology_invalid" in result.block_reasons


def test_blocks_invalid_schema_and_incomplete_review():
    rows = _findings()
    rows[0]["fingerprint"] = "invalid"
    rows[1]["review_status"] = "PENDING"
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(), rows, audit_timestamp=2000, scanned_line_count=10000,
    )
    assert "dead_code_finding_schema_invalid" in result.block_reasons
    assert "dead_code_finding_review_incomplete" in result.block_reasons


def test_blocks_ratio_excess_and_critical_dead_code():
    rows = _findings()
    rows[0]["dead_line_count"] = 400
    rows[0]["severity"] = "CRITICAL"
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(), rows, audit_timestamp=2000, scanned_line_count=1000,
    )
    assert "dead_code_ratio_exceeds_limit_or_scan_invalid" in result.block_reasons
    assert "critical_dead_code_detected" in result.block_reasons


def test_retained_code_is_not_actionable():
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(), _findings(), audit_timestamp=2000, scanned_line_count=10000,
    )
    assert result.expected_retention_count == 1
    assert "DEAD-003" in result.retained_finding_ids
    assert "DEAD-003" not in result.actionable_finding_ids
    assert result.cleanup_required is True


def test_certification_cleanup_and_execution_remain_controlled():
    rows = [_findings()[2]]
    result = ProductionDeadCodeAuditRuntime().audit(
        _duplicate(), rows, audit_timestamp=2000, scanned_line_count=10000,
    )
    assert result.cleanup_required is False
    assert result.source_removal_performed is False
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
