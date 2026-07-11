from dataclasses import FrozenInstanceError

import pytest

from afip.production_regression_audit import ProductionRegressionAuditRuntime


def _completion(**overrides):
    payload = {
        "completion_id": "QCOMP-1234567890ABCDEF", "status": "COMPLETE", "milestone": "Q", "pack": "10",
        "milestone_q_complete": True, "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "order_status": "NO_ORDER_SENT", "direct_execution": False,
        "live_execution_enabled": False, "production_certification_granted": False, "release_candidate_granted": False,
    }
    payload.update(overrides)
    return payload


def _policy():
    return {"broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01, "execution_status": "LOCKED_SIMULATION_ONLY",
            "order_status": "NO_ORDER_SENT", "direct_execution": False, "live_execution_enabled": False,
            "production_certification_granted": False, "release_candidate_granted": False}


def _evidence():
    rows = []
    for index in range(10):
        rows.append({"evidence_id": f"REGR-T{index:03d}", "evidence_type": "TARGETED_TEST", "timestamp": 1000 + index,
                     "status": "PASS", "passed": True, **_policy()})
    for index, name in enumerate(ProductionRegressionAuditRuntime.REQUIRED_CHECKS):
        rows.append({"evidence_id": f"REGR-C{index:03d}", "evidence_type": "REQUIRED_CHECK", "check_name": name,
                     "timestamp": 2000 + index, "status": "PASS", "passed": True, **_policy()})
    return rows


def test_regression_audit_passes_deterministically():
    result = ProductionRegressionAuditRuntime().audit(_completion(), _evidence(), audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert result.status == "PASS"
    assert result.regression_audit_passed is True
    assert result.regression_test_delta == 80
    assert result.next_audit == "R_DUPLICATE_CODE_AUDIT"


def test_report_is_immutable_and_repeatable():
    runtime = ProductionRegressionAuditRuntime()
    first = runtime.audit(_completion(), _evidence(), audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert first == runtime.audit(_completion(), _evidence(), audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_q_completion_lineage():
    result = ProductionRegressionAuditRuntime().audit(_completion(pack="9", milestone_q_complete=False), _evidence(), audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert "milestone_q_completion_lineage_invalid" in result.block_reasons


def test_blocks_regression_count_decrease():
    result = ProductionRegressionAuditRuntime().audit(_completion(), _evidence(), audit_timestamp=3000, baseline_test_count=1655, current_test_count=1600)
    assert "regression_test_count_invalid" in result.block_reasons


def test_blocks_duplicate_evidence_and_bad_chronology():
    rows = _evidence()
    rows[1]["evidence_id"] = rows[0]["evidence_id"]
    rows[2]["timestamp"] = 9999
    result = ProductionRegressionAuditRuntime().audit(_completion(), rows, audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert "duplicate_or_invalid_regression_evidence_id" in result.block_reasons
    assert "regression_audit_chronology_invalid" in result.block_reasons


def test_blocks_targeted_failure_or_insufficiency():
    rows = _evidence()
    rows[0].update(status="FAIL", passed=False)
    result = ProductionRegressionAuditRuntime().audit(_completion(), rows, audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert "targeted_regression_suite_failure_or_insufficiency" in result.block_reasons


def test_blocks_missing_required_check_and_policy_violation():
    rows = [row for row in _evidence() if row.get("check_name") != "MT5_DATA_CHECK"]
    rows[0]["broker"] = "OTHER"
    result = ProductionRegressionAuditRuntime().audit(_completion(), rows, audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert "required_regression_check_failed_or_missing" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons


def test_certification_release_and_execution_remain_disabled():
    result = ProductionRegressionAuditRuntime().audit(_completion(), _evidence(), audit_timestamp=3000, baseline_test_count=1575, current_test_count=1655)
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
