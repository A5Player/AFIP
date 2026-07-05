"""Release runtime for AFIP Production Milestone A Pack 13."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from afip.intelligence.compatibility_acceptance_assessment import CompatibilityAcceptanceAssessment
from afip.intelligence.production_evidence_index import ProductionEvidenceIndex
from afip.intelligence.release_quality_assessment import ReleaseQualityAssessment
from afip.learning.milestone_learning_archive import MilestoneLearningArchive


@dataclass(frozen=True)
class ProductionMilestoneAReleaseRuntimeResult:
    """Final Milestone A release runtime result."""

    status: str
    action: str
    release_score: float
    release_quality_score: float
    compatibility_score: float
    evidence_score: float
    learning_archive_score: float
    reason: str


class ProductionMilestoneAReleaseRuntime:
    """Evaluate final release acceptance for Production Milestone A."""

    def __init__(self) -> None:
        """Create a deterministic release runtime with additive dependencies."""
        self._release_quality = ReleaseQualityAssessment()
        self._compatibility = CompatibilityAcceptanceAssessment()
        self._evidence = ProductionEvidenceIndex()
        self._learning_archive = MilestoneLearningArchive()

    def evaluate(
        self,
        release_metrics: Mapping[str, float],
        compatibility_metrics: Mapping[str, float],
        evidence_metrics: Mapping[str, float],
        learning_metrics: Mapping[str, float],
    ) -> ProductionMilestoneAReleaseRuntimeResult:
        """Return final release readiness without changing trading execution behavior."""
        release_quality = self._release_quality.assess(release_metrics)
        compatibility = self._compatibility.assess(compatibility_metrics)
        evidence = self._evidence.evaluate(evidence_metrics)
        learning_archive = self._learning_archive.summarize(learning_metrics)

        release_score = round(
            release_quality.quality_score * 0.28
            + compatibility.acceptance_score * 0.26
            + evidence.evidence_score * 0.26
            + learning_archive.archive_score * 0.20,
            4,
        )

        release_ready = (
            release_quality.status == "RELEASE_QUALITY_READY"
            and compatibility.status == "COMPATIBILITY_ACCEPTED"
            and evidence.status == "PRODUCTION_EVIDENCE_COMPLETE"
            and learning_archive.status == "LEARNING_ARCHIVE_READY"
        )

        if release_ready and release_score >= 0.84:
            status = "MILESTONE_A_RELEASE_READY"
            action = "PREPARE_PRODUCTION_MILESTONE_A_FINAL_REPORT"
            reason = "all_release_acceptance_inputs_ready"
        elif release_score >= 0.66:
            status = "MILESTONE_A_RELEASE_REVIEW"
            action = "CONTINUE_RELEASE_ACCEPTANCE_REVIEW"
            reason = "release_acceptance_inputs_require_review"
        else:
            status = "MILESTONE_A_RELEASE_NOT_READY"
            action = "KEEP_SIMULATION_ONLY"
            reason = "release_acceptance_inputs_below_threshold"

        return ProductionMilestoneAReleaseRuntimeResult(
            status=status,
            action=action,
            release_score=release_score,
            release_quality_score=release_quality.quality_score,
            compatibility_score=compatibility.acceptance_score,
            evidence_score=evidence.evidence_score,
            learning_archive_score=learning_archive.archive_score,
            reason=reason,
        )
