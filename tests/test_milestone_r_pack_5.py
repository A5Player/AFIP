from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from afip.production_repository_cleanup import ProductionRepositoryCleanupRuntime


def _architecture(**overrides):
    payload = {
        "audit_id": "ARAUD-1234567890ABCDEF", "status": "PASS", "milestone": "R", "pack": "4",
        "architecture_audit_passed": True, "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
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


def _actions():
    return [
        {"action_id": "CLEAN-001", "timestamp": 1000, "action_kind": "CACHE_ARTIFACT",
         "target_path": ".pytest_cache", "fingerprint": _fp("cache"), "protected_source": False,
         "cleanup_authorized": True, "review_status": "REVIEWED", "completion_status": "COMPLETED", **_policy()},
        {"action_id": "CLEAN-002", "timestamp": 1001, "action_kind": "GENERATED_ARTIFACT",
         "target_path": "runtime/dashboard/temporary.html", "fingerprint": _fp("generated"), "protected_source": False,
         "cleanup_authorized": True, "review_status": "ACCEPTED", "completion_status": "COMPLETED", **_policy()},
        {"action_id": "CLEAN-003", "timestamp": 1002, "action_kind": "POLICY_RETAINED",
         "target_path": "afip/compatibility/legacy_api.py", "fingerprint": _fp("retained"), "protected_source": True,
         "cleanup_authorized": False, "review_status": "ACCEPTED", "completion_status": "RETAINED", **_policy()},
    ]


def test_repository_cleanup_passes_deterministically():
    result = ProductionRepositoryCleanupRuntime().validate(_architecture(), _actions(), cleanup_timestamp=2000)
    assert result.status == "PASS"
    assert result.repository_cleanup_passed is True
    assert result.authorized_action_count == 2
    assert result.completed_action_count == 2
    assert result.next_audit == "R_SAFETY_AUDIT"


def test_report_is_immutable_and_repeatable():
    runtime = ProductionRepositoryCleanupRuntime()
    first = runtime.validate(_architecture(), _actions(), cleanup_timestamp=2000)
    second = runtime.validate(_architecture(), _actions(), cleanup_timestamp=2000)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_blocks_invalid_architecture_lineage():
    result = ProductionRepositoryCleanupRuntime().validate(
        _architecture(pack="3", architecture_audit_passed=False), _actions(), cleanup_timestamp=2000,
    )
    assert "architecture_audit_lineage_invalid" in result.block_reasons


def test_blocks_duplicate_ids_and_bad_chronology():
    rows = _actions()
    rows[1]["action_id"] = rows[0]["action_id"]
    rows[2]["timestamp"] = 9999
    result = ProductionRepositoryCleanupRuntime().validate(_architecture(), rows, cleanup_timestamp=2000)
    assert "duplicate_or_invalid_cleanup_action_id" in result.block_reasons
    assert "repository_cleanup_chronology_invalid" in result.block_reasons


def test_blocks_invalid_schema_and_incomplete_review():
    rows = _actions()
    rows[0]["fingerprint"] = "invalid"
    rows[1]["review_status"] = "PENDING"
    result = ProductionRepositoryCleanupRuntime().validate(_architecture(), rows, cleanup_timestamp=2000)
    assert "repository_cleanup_action_schema_invalid" in result.block_reasons
    assert "repository_cleanup_review_incomplete" in result.block_reasons


def test_blocks_incomplete_authorized_cleanup():
    rows = _actions()
    rows[0]["completion_status"] = "RETAINED"
    result = ProductionRepositoryCleanupRuntime().validate(_architecture(), rows, cleanup_timestamp=2000)
    assert "authorized_cleanup_action_incomplete" in result.block_reasons


def test_protected_source_is_never_authorized_for_cleanup():
    rows = _actions()
    rows[0]["protected_source"] = True
    rows[0]["cleanup_authorized"] = True
    result = ProductionRepositoryCleanupRuntime().validate(_architecture(), rows, cleanup_timestamp=2000)
    assert "protected_source_cleanup_attempt_detected" in result.block_reasons
    assert "CLEAN-001" not in result.authorized_action_ids
    assert result.no_protected_source_targeted is False


def test_certification_runtime_and_trading_logic_remain_locked():
    result = ProductionRepositoryCleanupRuntime().validate(_architecture(), _actions(), cleanup_timestamp=2000)
    assert result.production_certification_granted is False
    assert result.release_candidate_granted is False
    assert result.trading_logic_changed is False
    assert result.dependency_wiring_changed is False
    assert result.protected_source_removed is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"
    assert result.broker_request_created is False
    assert result.order_transmission_attempted is False
    assert result.position_modification_attempted is False
