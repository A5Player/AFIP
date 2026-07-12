from dataclasses import FrozenInstanceError
import pytest
from afip.version_1_release_record import Version1ReleaseRecordRuntime


def final_review(**overrides):
    row = {
        "final_review_id": "V1FINAL-1234567890ABCDEF", "status": "APPROVED",
        "reason": "VERSION_1_FINAL_REVIEW_APPROVED", "milestone": "R", "pack": "13",
        "review_timestamp": 500, "production_certification_granted": True,
        "release_candidate_granted": True, "version_1_final_granted": True, "version": "1.0",
        "broker": "XM", "symbol": "GOLD#", "base_lot_per_unit": 0.01,
        "execution_status": "LOCKED_SIMULATION_ONLY", "direct_execution": False,
        "live_execution_enabled": False, "order_status": "NO_ORDER_SENT",
    }
    row.update(overrides)
    return row


def validations():
    return {key: True for key in Version1ReleaseRecordRuntime.REQUIRED_VALIDATIONS}


def documents():
    return {key: True for key in Version1ReleaseRecordRuntime.REQUIRED_DOCUMENTS}


def metadata():
    return {
        "VERSION": "1.0", "RELEASE_NAME": "AFIP_VERSION_1_0_FINAL", "RELEASE_STATUS": "FINAL",
        "BROKER_POLICY": "XM_ONLY", "SYMBOL_POLICY": "GOLD#_ONLY",
        "BASE_UNIT_POLICY": "1_UNIT_EQUALS_0.01_LOT", "EXECUTION_POLICY": "LOCKED_SIMULATION_ONLY",
    }


def create(**kwargs):
    return Version1ReleaseRecordRuntime().create(
        kwargs.pop("reports", [final_review()]), release_timestamp=kwargs.pop("release_timestamp", 600),
        validation_manifest=kwargs.pop("validation_manifest", validations()),
        documentation_manifest=kwargs.pop("documentation_manifest", documents()),
        release_metadata=kwargs.pop("release_metadata", metadata()), **kwargs,
    )


def test_release_record_granted_with_execution_lock():
    result = create()
    assert result.status == "RELEASED"
    assert result.version == "1.0"
    assert result.release_record_granted is True
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"
    assert result.live_execution_enabled is False


def test_deterministic_and_immutable():
    first, second = create(), create()
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_duplicate_or_invalid_final_review_blocks():
    result = create(reports=[final_review(), final_review()])
    assert "duplicate_or_invalid_final_review_id" in result.block_reasons
    assert "version_1_final_identity_not_confirmed" in result.block_reasons


def test_future_or_invalid_schema_blocks():
    result = create(reports=[final_review(review_timestamp=700, status="BLOCKED")])
    assert "release_record_chronology_invalid" in result.block_reasons
    assert "final_review_schema_invalid" in result.block_reasons


def test_incomplete_validation_blocks():
    manifest = validations(); manifest["FULL_PYTEST"] = False
    assert "release_validation_manifest_incomplete" in create(validation_manifest=manifest).block_reasons


def test_incomplete_documentation_blocks():
    manifest = documents(); manifest["README_TH"] = False
    assert "release_documentation_manifest_incomplete" in create(documentation_manifest=manifest).block_reasons


def test_invalid_metadata_or_unlock_attempt_blocks():
    meta = metadata(); meta["BROKER_POLICY"] = "MULTI_BROKER"
    result = create(release_metadata=meta, reports=[final_review(execution_unlock_authorized=True)])
    assert "release_metadata_invalid" in result.block_reasons
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons
    assert result.live_execution_enabled is False


def test_as_dict_preserves_final_release_boundary():
    data = create().as_dict()
    assert data["release_record_granted"] is True
    assert data["version"] == "1.0"
    assert data["direct_execution"] is False
    assert data["order_status"] == "NO_ORDER_SENT"
