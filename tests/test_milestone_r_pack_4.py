from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from afip.production_certification_architecture_audit import ProductionArchitectureAuditRuntime


def _dead(**overrides):
    payload = {
        "audit_id": "DCAUD-1234567890ABCDEF", "status": "PASS", "milestone": "R", "pack": "3",
        "dead_code_audit_passed": True, "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
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


def _fp(value):
    return sha256(value.encode()).hexdigest()


def _findings():
    return [
        {"finding_id": "ARCH-001", "timestamp": 1000, "architecture_kind": "BOUNDARY_VIOLATION",
         "severity": "LOW", "fingerprint": _fp("a"), "source_component": "domain", "target_component": "ui",
         "accepted_exception": False, "review_status": "REMEDIATION_REQUIRED", **_policy()},
        {"finding_id": "ARCH-002", "timestamp": 1001, "architecture_kind": "DEPENDENCY_DIRECTION",
         "severity": "MEDIUM", "fingerprint": _fp("b"), "source_component": "knowledge", "target_component": "execution",
         "accepted_exception": False, "review_status": "REMEDIATION_REQUIRED", **_policy()},
        {"finding_id": "ARCH-003", "timestamp": 1002, "architecture_kind": "ACCEPTED_EXCEPTION",
         "severity": "INFO", "fingerprint": _fp("c"), "source_component": "compatibility", "target_component": "legacy_api",
         "accepted_exception": True, "review_status": "ACCEPTED", **_policy()},
    ]


def test_architecture_audit_passes_deterministically():
    result = ProductionArchitectureAuditRuntime().audit(
        _dead(), _findings(), audit_timestamp=2000, inspected_component_count=20,
    )
    assert result.status == "PASS"
    assert result.architecture_audit_passed is True
    assert result.actionable_architecture_count == 2
    assert result.architecture_score == 0.9625
    assert result.next_audit == "R_REPOSITORY_CLEANUP"


def test_report_is_immutable_and_repeatable():
    runtime = ProductionArchitectureAuditRuntime()
    first = runtime.audit(_dead(), _findings(), audit_timestamp=2000, inspected_component_count=20)
    second = runtime.audit(_dead(), _findings(), audit_timestamp=2000, inspected_component_count=20)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_dead_code_lineage():
    result = ProductionArchitectureAuditRuntime().audit(
        _dead(pack="2", dead_code_audit_passed=False), _findings(), audit_timestamp=2000, inspected_component_count=20,
    )
    assert "dead_code_audit_lineage_invalid" in result.block_reasons


def test_blocks_duplicate_ids_and_bad_chronology():
    rows = _findings()
    rows[1]["finding_id"] = rows[0]["finding_id"]
    rows[2]["timestamp"] = 9999
    result = ProductionArchitectureAuditRuntime().audit(_dead(), rows, audit_timestamp=2000, inspected_component_count=20)
    assert "duplicate_or_invalid_architecture_finding_id" in result.block_reasons
    assert "architecture_audit_chronology_invalid" in result.block_reasons


def test_blocks_invalid_schema_and_incomplete_review():
    rows = _findings()
    rows[0]["fingerprint"] = "invalid"
    rows[1]["review_status"] = "PENDING"
    result = ProductionArchitectureAuditRuntime().audit(_dead(), rows, audit_timestamp=2000, inspected_component_count=20)
    assert "architecture_finding_schema_invalid" in result.block_reasons
    assert "architecture_finding_review_incomplete" in result.block_reasons


def test_blocks_low_score_and_critical_violation():
    rows = _findings()
    rows[0]["severity"] = "CRITICAL"
    result = ProductionArchitectureAuditRuntime().audit(
        _dead(), rows, audit_timestamp=2000, inspected_component_count=2, minimum_architecture_score=0.90,
    )
    assert "architecture_score_below_minimum_or_component_count_invalid" in result.block_reasons
    assert "critical_architecture_violation_detected" in result.block_reasons


def test_accepted_exception_is_not_actionable():
    result = ProductionArchitectureAuditRuntime().audit(_dead(), _findings(), audit_timestamp=2000, inspected_component_count=20)
    assert result.expected_exception_count == 1
    assert "ARCH-003" in result.accepted_exception_ids
    assert "ARCH-003" not in result.actionable_finding_ids
    assert result.cleanup_required is True


def test_certification_cleanup_and_execution_remain_controlled():
    rows = [_findings()[2]]
    result = ProductionArchitectureAuditRuntime().audit(_dead(), rows, audit_timestamp=2000, inspected_component_count=20)
    assert result.cleanup_required is False
    assert result.architecture_change_performed is False
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
