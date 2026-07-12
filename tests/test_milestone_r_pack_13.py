from dataclasses import FrozenInstanceError
import pytest
from afip.version_1_final_review import Version1FinalReviewRuntime


def release_candidate(**overrides):
    row = {
        "review_id": "RCREV-1234567890ABCDEF",
        "status": "APPROVED",
        "reason": "RELEASE_CANDIDATE_REVIEW_APPROVED",
        "milestone": "R",
        "pack": "12",
        "review_timestamp": 400,
        "release_candidate_granted": True,
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


def reviewers():
    return {key: True for key in Version1FinalReviewRuntime.REQUIRED_FINAL_REVIEWERS}


def validations():
    return {key: True for key in Version1FinalReviewRuntime.REQUIRED_VALIDATIONS}


def documents():
    return {key: True for key in (
        "README_EN", "README_TH", "AFIP_PROJECT_DATABASE", "HANDOFF", "FILE_LIST", "VALIDATION_RECORD"
    )}


def review(**kwargs):
    return Version1FinalReviewRuntime().review(
        kwargs.pop("reports", [release_candidate()]),
        review_timestamp=kwargs.pop("review_timestamp", 500),
        final_reviewer_manifest=kwargs.pop("final_reviewer_manifest", reviewers()),
        validation_manifest=kwargs.pop("validation_manifest", validations()),
        documentation_manifest=kwargs.pop("documentation_manifest", documents()),
        **kwargs,
    )


def test_review_grants_version_1_final_only_with_execution_lock():
    result = review()
    assert result.status == "APPROVED"
    assert result.production_certification_granted is True
    assert result.release_candidate_granted is True
    assert result.version_1_final_granted is True
    assert result.version == "1.0"
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"


def test_deterministic_and_immutable():
    first = review()
    second = review()
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_invalid_or_duplicate_release_candidate_blocks():
    result = review(reports=[release_candidate(), release_candidate()])
    assert "duplicate_or_invalid_release_candidate_id" in result.block_reasons
    assert "release_candidate_not_confirmed" in result.block_reasons


def test_future_or_invalid_schema_blocks():
    result = review(reports=[release_candidate(review_timestamp=600, status="BLOCKED")])
    assert "version_1_final_review_chronology_invalid" in result.block_reasons
    assert "release_candidate_schema_invalid" in result.block_reasons


def test_incomplete_final_reviewer_manifest_blocks():
    manifest = reviewers()
    manifest["SECURITY_FINAL_REVIEW"] = False
    result = review(final_reviewer_manifest=manifest)
    assert "version_1_final_reviewer_manifest_incomplete" in result.block_reasons


def test_incomplete_validation_and_documentation_blocks():
    validation = validations()
    validation["FULL_PYTEST"] = False
    documentation = documents()
    documentation["README_TH"] = False
    result = review(validation_manifest=validation, documentation_manifest=documentation)
    assert "version_1_final_validation_manifest_incomplete" in result.block_reasons
    assert "version_1_final_documentation_manifest_incomplete" in result.block_reasons


def test_policy_violation_blocks_unlock_attempt():
    result = review(reports=[release_candidate(execution_unlock_authorized=True)])
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons
    assert result.version_1_final_granted is False
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"


def test_as_dict_preserves_release_and_execution_boundary():
    data = review().as_dict()
    assert data["version_1_final_granted"] is True
    assert data["version"] == "1.0"
    assert data["execution_unlock_authorized"] is False
    assert data["live_execution_enabled"] is False
