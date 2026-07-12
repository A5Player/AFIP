from dataclasses import FrozenInstanceError
import pytest
from afip.release_candidate_review import ReleaseCandidateReviewRuntime


def preparation(**overrides):
    row = {
        "preparation_id": "RCPREP-1234567890ABCDEF",
        "status": "PREPARED",
        "reason": "RELEASE_CANDIDATE_PREPARATION_COMPLETE",
        "milestone": "R",
        "pack": "11",
        "preparation_timestamp": 300,
        "release_candidate_prepared": True,
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


def reviewers():
    return {key: True for key in ReleaseCandidateReviewRuntime.REQUIRED_REVIEWERS}


def validations():
    return {key: True for key in ReleaseCandidateReviewRuntime.REQUIRED_VALIDATIONS}


def documents():
    return {key: True for key in (
        "README_EN", "README_TH", "AFIP_PROJECT_DATABASE", "HANDOFF", "FILE_LIST", "VALIDATION_RECORD"
    )}


def review(**kwargs):
    return ReleaseCandidateReviewRuntime().review(
        kwargs.pop("reports", [preparation()]),
        review_timestamp=kwargs.pop("review_timestamp", 400),
        reviewer_manifest=kwargs.pop("reviewer_manifest", reviewers()),
        validation_manifest=kwargs.pop("validation_manifest", validations()),
        documentation_manifest=kwargs.pop("documentation_manifest", documents()),
        **kwargs,
    )


def test_review_approves_release_candidate_only():
    result = review()
    assert result.status == "APPROVED"
    assert result.release_candidate_granted is True
    assert result.version_1_final_granted is False
    assert result.execution_status == "LOCKED_SIMULATION_ONLY"


def test_deterministic_and_immutable():
    first = review()
    second = review()
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.status = "BLOCKED"


def test_invalid_or_duplicate_preparation_blocks():
    result = review(reports=[preparation(), preparation()])
    assert "duplicate_or_invalid_preparation_id" in result.block_reasons
    assert "release_candidate_preparation_not_confirmed" in result.block_reasons


def test_future_or_invalid_schema_blocks():
    result = review(reports=[preparation(preparation_timestamp=500, status="BLOCKED")])
    assert "release_candidate_review_chronology_invalid" in result.block_reasons
    assert "release_candidate_preparation_schema_invalid" in result.block_reasons


def test_incomplete_reviewer_manifest_blocks():
    manifest = reviewers()
    manifest["SECURITY_REVIEW"] = False
    result = review(reviewer_manifest=manifest)
    assert "release_candidate_reviewer_manifest_incomplete" in result.block_reasons


def test_incomplete_validation_and_documentation_blocks():
    validation = validations()
    validation["FULL_PYTEST"] = False
    documentation = documents()
    documentation["README_TH"] = False
    result = review(validation_manifest=validation, documentation_manifest=documentation)
    assert "release_candidate_review_validation_manifest_incomplete" in result.block_reasons
    assert "release_candidate_review_documentation_manifest_incomplete" in result.block_reasons


def test_policy_violation_blocks_unlock_attempt():
    result = review(reports=[preparation(execution_unlock_authorized=True)])
    assert "feature_freeze_or_execution_policy_violation" in result.block_reasons
    assert result.release_candidate_granted is False
    assert result.direct_execution is False
    assert result.live_execution_enabled is False
    assert result.order_status == "NO_ORDER_SENT"


def test_as_dict_preserves_final_boundary():
    data = review().as_dict()
    assert data["release_candidate_granted"] is True
    assert data["version_1_final_granted"] is False
    assert data["execution_unlock_authorized"] is False
