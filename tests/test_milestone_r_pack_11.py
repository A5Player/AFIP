from dataclasses import FrozenInstanceError
import pytest
from afip.release_candidate_preparation import ReleaseCandidatePreparationRuntime


def certification(**overrides):
    row = {
        "certification_id": "RCERT-1234567890ABCDEF",
        "status": "CERTIFIED",
        "reason": "PRODUCTION_CERTIFICATION_GRANTED",
        "milestone": "R",
        "pack": "10",
        "certification_timestamp": 200,
        "production_certification_granted": True,
        "release_candidate_granted": False,
        "version_1_final_granted": False,
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


def artifacts():
    return {key: True for key in ReleaseCandidatePreparationRuntime.REQUIRED_ARTIFACTS}


def validations():
    return {key: True for key in ReleaseCandidatePreparationRuntime.REQUIRED_VALIDATIONS}


def documents():
    return {"README_EN": True, "README_TH": True, "AFIP_PROJECT_DATABASE": True, "HANDOFF": True}


def prepare(**kwargs):
    return ReleaseCandidatePreparationRuntime().prepare(
        kwargs.pop("reports", [certification()]),
        preparation_timestamp=kwargs.pop("preparation_timestamp", 300),
        artifact_manifest=kwargs.pop("artifact_manifest", artifacts()),
        validation_manifest=kwargs.pop("validation_manifest", validations()),
        documentation_manifest=kwargs.pop("documentation_manifest", documents()),
        **kwargs,
    )


def test_preparation_complete_but_candidate_not_granted():
    result = prepare()
    assert result.status == "PREPARED"
    assert result.release_candidate_prepared is True
    assert result.release_candidate_granted is False
    assert result.version_1_final_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"


def test_deterministic_and_immutable():
    first = prepare()
    second = prepare()
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_invalid_or_duplicate_certification_blocks():
    result = prepare(reports=[certification(), certification()])
    assert "duplicate_or_invalid_certification_id" in result.block_reasons
    assert "production_certification_not_confirmed" in result.block_reasons


def test_future_or_invalid_schema_blocks():
    result = prepare(reports=[certification(certification_timestamp=400, status="BLOCKED")])
    assert "release_candidate_chronology_invalid" in result.block_reasons
    assert "production_certification_schema_invalid" in result.block_reasons


def test_incomplete_artifact_manifest_blocks():
    manifest = artifacts()
    manifest["RUN_PS1"] = False
    result = prepare(artifact_manifest=manifest)
    assert "release_candidate_artifact_manifest_incomplete" in result.block_reasons


def test_incomplete_validation_and_documentation_blocks():
    validation = validations()
    validation["FULL_PYTEST"] = False
    documentation = documents()
    documentation["README_TH"] = False
    result = prepare(validation_manifest=validation, documentation_manifest=documentation)
    assert "release_candidate_validation_manifest_incomplete" in result.block_reasons
    assert "release_candidate_documentation_manifest_incomplete" in result.block_reasons


def test_policy_violation_blocks_unlock_attempt():
    result = prepare(reports=[certification(execution_unlock_authorized=True)])
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"


def test_as_dict_preserves_release_boundaries():
    data = prepare().as_dict()
    assert data["release_candidate_prepared"] is True
    assert data["release_candidate_granted"] is False
    assert data["version_1_final_granted"] is False
    assert data["execution_unlock_authorized"] is False
