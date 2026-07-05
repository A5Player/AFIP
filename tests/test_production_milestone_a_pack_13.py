"""Tests for AFIP Production Milestone A Pack 13."""

from afip.intelligence.compatibility_acceptance_assessment import CompatibilityAcceptanceAssessment
from afip.intelligence.production_evidence_index import ProductionEvidenceIndex
from afip.intelligence.release_quality_assessment import ReleaseQualityAssessment
from afip.learning.milestone_learning_archive import MilestoneLearningArchive
from afip.runtime.production_milestone_a_release_runtime import ProductionMilestoneAReleaseRuntime


def test_release_quality_assessment_ready_status() -> None:
    result = ReleaseQualityAssessment().assess(
        {
            "validation_quality": 0.94,
            "documentation_quality": 0.90,
            "runtime_quality": 0.92,
            "compatibility_quality": 0.96,
            "naming_quality": 1.00,
            "regression_pressure": 0.04,
        }
    )
    assert result.status == "RELEASE_QUALITY_READY"
    assert result.action == "PREPARE_MILESTONE_A_RELEASE"
    assert result.quality_score >= 0.82


def test_release_quality_assessment_keeps_simulation_when_quality_is_low() -> None:
    result = ReleaseQualityAssessment().assess(
        {
            "validation_quality": 0.32,
            "documentation_quality": 0.30,
            "runtime_quality": 0.35,
            "compatibility_quality": 0.40,
            "naming_quality": 0.45,
            "regression_pressure": 0.80,
        }
    )
    assert result.status == "RELEASE_QUALITY_NOT_READY"
    assert result.action == "KEEP_SIMULATION_ONLY"


def test_compatibility_acceptance_assessment_accepts_additive_release() -> None:
    result = CompatibilityAcceptanceAssessment().assess(
        {
            "api_stability": 0.96,
            "import_stability": 0.94,
            "ci_alignment": 0.98,
            "simulation_continuity": 0.96,
            "additive_design": 1.00,
            "compatibility_pressure": 0.05,
        }
    )
    assert result.status == "COMPATIBILITY_ACCEPTED"
    assert result.action == "ACCEPT_RELEASE_COMPATIBILITY"


def test_compatibility_acceptance_assessment_requires_review_under_pressure() -> None:
    result = CompatibilityAcceptanceAssessment().assess(
        {
            "api_stability": 0.76,
            "import_stability": 0.74,
            "ci_alignment": 0.78,
            "simulation_continuity": 0.76,
            "additive_design": 0.80,
            "compatibility_pressure": 0.22,
        }
    )
    assert result.status == "COMPATIBILITY_REVIEW"
    assert result.action == "CONTINUE_COMPATIBILITY_VALIDATION"


def test_production_evidence_index_complete_status() -> None:
    result = ProductionEvidenceIndex().evaluate(
        {
            "test_evidence": 0.98,
            "quality_evidence": 0.96,
            "runtime_evidence": 0.94,
            "documentation_evidence": 0.92,
            "naming_evidence": 1.00,
            "evidence_gap": 0.04,
        }
    )
    assert result.status == "PRODUCTION_EVIDENCE_COMPLETE"
    assert result.action == "ACCEPT_MILESTONE_A_EVIDENCE"


def test_milestone_learning_archive_ready_status() -> None:
    result = MilestoneLearningArchive().summarize(
        {
            "calibration_history": 0.90,
            "optimization_history": 0.92,
            "confidence_history": 0.90,
            "stability_history": 0.88,
            "documentation_history": 0.86,
            "learning_gap": 0.08,
        }
    )
    assert result.status == "LEARNING_ARCHIVE_READY"
    assert result.action == "INCLUDE_LEARNING_RECORD_IN_RELEASE"


def test_release_runtime_prepares_final_report() -> None:
    result = ProductionMilestoneAReleaseRuntime().evaluate(
        release_metrics={
            "validation_quality": 0.96,
            "documentation_quality": 0.92,
            "runtime_quality": 0.94,
            "compatibility_quality": 0.98,
            "naming_quality": 1.00,
            "regression_pressure": 0.03,
        },
        compatibility_metrics={
            "api_stability": 0.96,
            "import_stability": 0.94,
            "ci_alignment": 0.98,
            "simulation_continuity": 0.96,
            "additive_design": 1.00,
            "compatibility_pressure": 0.04,
        },
        evidence_metrics={
            "test_evidence": 0.98,
            "quality_evidence": 0.96,
            "runtime_evidence": 0.94,
            "documentation_evidence": 0.92,
            "naming_evidence": 1.00,
            "evidence_gap": 0.04,
        },
        learning_metrics={
            "calibration_history": 0.90,
            "optimization_history": 0.92,
            "confidence_history": 0.90,
            "stability_history": 0.88,
            "documentation_history": 0.86,
            "learning_gap": 0.08,
        },
    )
    assert result.status == "MILESTONE_A_RELEASE_READY"
    assert result.action == "PREPARE_PRODUCTION_MILESTONE_A_FINAL_REPORT"
    assert result.release_score >= 0.84


def test_release_runtime_preserves_simulation_only_mode_when_not_ready() -> None:
    result = ProductionMilestoneAReleaseRuntime().evaluate(
        release_metrics={
            "validation_quality": 0.30,
            "documentation_quality": 0.28,
            "runtime_quality": 0.34,
            "compatibility_quality": 0.36,
            "naming_quality": 0.50,
            "regression_pressure": 0.82,
        },
        compatibility_metrics={
            "api_stability": 0.30,
            "import_stability": 0.32,
            "ci_alignment": 0.34,
            "simulation_continuity": 0.36,
            "additive_design": 0.38,
            "compatibility_pressure": 0.78,
        },
        evidence_metrics={
            "test_evidence": 0.30,
            "quality_evidence": 0.32,
            "runtime_evidence": 0.34,
            "documentation_evidence": 0.30,
            "naming_evidence": 0.42,
            "evidence_gap": 0.80,
        },
        learning_metrics={
            "calibration_history": 0.30,
            "optimization_history": 0.32,
            "confidence_history": 0.30,
            "stability_history": 0.28,
            "documentation_history": 0.34,
            "learning_gap": 0.76,
        },
    )
    assert result.status == "MILESTONE_A_RELEASE_NOT_READY"
    assert result.action == "KEEP_SIMULATION_ONLY"
