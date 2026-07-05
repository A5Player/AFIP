"""Milestone learning archive for AFIP Production Milestone A Pack 13."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def _ratio(value: float) -> float:
    """Return a bounded ratio for learning archive scoring."""
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class MilestoneLearningArchiveResult:
    """Learning archive result for milestone release continuity."""

    archive_score: float
    status: str
    action: str
    reason: str


class MilestoneLearningArchive:
    """Summarize learning continuity for milestone release preparation."""

    def summarize(self, metrics: Mapping[str, float]) -> MilestoneLearningArchiveResult:
        """Return learning archive readiness for release records."""
        calibration_history = _ratio(metrics.get("calibration_history", 0.50))
        optimization_history = _ratio(metrics.get("optimization_history", 0.50))
        confidence_history = _ratio(metrics.get("confidence_history", 0.50))
        stability_history = _ratio(metrics.get("stability_history", 0.50))
        documentation_history = _ratio(metrics.get("documentation_history", 0.50))
        learning_gap = _ratio(metrics.get("learning_gap", 0.50))

        raw_score = (
            calibration_history * 0.20
            + optimization_history * 0.22
            + confidence_history * 0.20
            + stability_history * 0.20
            + documentation_history * 0.18
        )
        archive_score = _ratio(raw_score * (1.0 - learning_gap * 0.24))

        if archive_score >= 0.82 and learning_gap <= 0.18:
            status = "LEARNING_ARCHIVE_READY"
            action = "INCLUDE_LEARNING_RECORD_IN_RELEASE"
            reason = "learning_archive_supports_milestone_release"
        elif archive_score >= 0.64:
            status = "LEARNING_ARCHIVE_REVIEW"
            action = "CONTINUE_LEARNING_RECORD_REVIEW"
            reason = "learning_archive_requires_review"
        else:
            status = "LEARNING_ARCHIVE_INCOMPLETE"
            action = "KEEP_LEARNING_RECORD_IN_VALIDATION"
            reason = "learning_archive_below_release_threshold"

        return MilestoneLearningArchiveResult(
            archive_score=round(archive_score, 4),
            status=status,
            action=action,
            reason=reason,
        )
