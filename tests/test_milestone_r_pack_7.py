from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from afip.production_certification_security_audit import ProductionSecurityAuditRuntime


def safety_report(**overrides):
    row = {
        "milestone": "R",
        "pack": "6",
        "status": "PASS",
        "safety_audit_passed": True,
        "audit_id": "RSAFE-1234567890ABCDEF",
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


def control(control_id, domain, **overrides):
    row = {
        "control_id": control_id,
        "control_domain": domain,
        "result": "PASS",
        "severity": "HIGH",
        "review_status": "REVIEWED",
        "timestamp": 100,
        "description": f"Reviewed {domain.lower()} control",
        "fingerprint": sha256(f"{control_id}:{domain}".encode()).hexdigest(),
        "exception_accepted": False,
        "broker": "XM",
        "symbol": "GOLD#",
        "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY",
        "direct_execution": False,
        "live_execution_enabled": False,
        "order_status": "NO_ORDER_SENT",
        "credential_value_collected": False,
        "secret_value_exposed": False,
        "dependency_changed": False,
        "network_configuration_changed": False,
        "broker_request_created": False,
        "order_transmission_attempted": False,
        "position_modification_attempted": False,
        "trading_logic_changed": False,
    }
    row.update(overrides)
    return row


def controls():
    domains = (
        "CREDENTIAL_SECURITY",
        "SECRET_EXPOSURE",
        "INPUT_VALIDATION",
        "DEPENDENCY_INTEGRITY",
        "FILE_CONFIGURATION",
        "NETWORK_BOUNDARY",
        "AUDIT_LOGGING",
    )
    return [control(f"SEC-{index:03d}", domain) for index, domain in enumerate(domains, 1)]


def test_security_audit_passes_complete_reviewed_evidence():
    report = ProductionSecurityAuditRuntime().validate(safety_report(), controls(), audit_timestamp=200)
    assert report.status == "PASS"
    assert report.security_audit_passed is True
    assert report.security_score == 1.0
    assert report.mandatory_domains_covered is True
    assert report.next_audit == "R_DATA_INTEGRITY_AUDIT"


def test_security_report_is_deterministic_and_immutable():
    runtime = ProductionSecurityAuditRuntime()
    first = runtime.validate(safety_report(), controls(), audit_timestamp=200)
    second = runtime.validate(safety_report(), controls(), audit_timestamp=200)
    assert first == second
    assert first.audit_id.startswith("RSEC-")
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_security_audit_blocks_invalid_safety_lineage():
    report = ProductionSecurityAuditRuntime().validate(
        safety_report(safety_audit_passed=False), controls(), audit_timestamp=200
    )
    assert report.status == "BLOCKED"
    assert "safety_audit_lineage_invalid" in report.block_reasons


def test_security_audit_blocks_duplicate_ids_and_future_evidence():
    rows = controls()
    rows[1]["control_id"] = rows[0]["control_id"]
    rows[2]["timestamp"] = 300
    report = ProductionSecurityAuditRuntime().validate(safety_report(), rows, audit_timestamp=200)
    assert "duplicate_or_invalid_security_control_id" in report.block_reasons
    assert "security_audit_chronology_invalid" in report.block_reasons


def test_security_audit_blocks_missing_domain_and_bad_schema():
    rows = controls()[:-1]
    rows[0]["fingerprint"] = "not-a-sha256"
    report = ProductionSecurityAuditRuntime().validate(safety_report(), rows, audit_timestamp=200)
    assert "mandatory_security_domain_missing" in report.block_reasons
    assert "security_control_schema_invalid" in report.block_reasons


def test_security_audit_blocks_unreviewed_and_unaccepted_failure():
    rows = controls()
    rows[0]["review_status"] = "REJECTED"
    rows[1]["result"] = "FAIL"
    report = ProductionSecurityAuditRuntime().validate(safety_report(), rows, audit_timestamp=200)
    assert "security_control_review_incomplete" in report.block_reasons
    assert "unaccepted_security_control_failure" in report.block_reasons


def test_security_audit_blocks_critical_failure_and_low_score():
    rows = controls()
    rows[0].update(result="FAIL", severity="CRITICAL", exception_accepted=True)
    report = ProductionSecurityAuditRuntime().validate(
        safety_report(), rows, audit_timestamp=200, minimum_security_score=0.95
    )
    assert "critical_security_control_failure" in report.block_reasons
    assert "security_score_below_threshold" in report.block_reasons


def test_security_audit_preserves_execution_and_secret_boundaries():
    rows = controls()
    rows[0]["secret_value_exposed"] = True
    report = ProductionSecurityAuditRuntime().validate(safety_report(), rows, audit_timestamp=200)
    assert "feature_freeze_or_execution_policy_violation" in report.block_reasons
    assert report.execution_status == "LOCKED_SIMULATION_ONLY"
    assert report.direct_execution is False
    assert report.live_execution_enabled is False
    assert report.order_status == "NO_ORDER_SENT"
    assert report.production_certification_granted is False
    assert report.release_candidate_granted is False
    assert report.credential_value_collected is False
    assert report.secret_value_exposed is False
